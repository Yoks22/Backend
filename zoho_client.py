import requests, time, traceback, json
from models import db, Contact, Account, Pipeline, Call, Event, Task, Note, SyncLog
from datetime import datetime
from dateutil import parser as date_parser


class ZohoClient:
    def __init__(self, cfg):
        self.cfg = cfg
        self.access_token = cfg.ACCESS_TOKEN
        self.refresh_token = cfg.REFRESH_TOKEN
        self.token_url = cfg.TOKEN_URL
        self.base_url = cfg.BASE_URL

    def _log(self, module):
        log = SyncLog(module=module, started_at=datetime.utcnow(), status='running')
        db.session.add(log)
        db.session.commit()
        return log

    def _finish(self, log, status, message='', records=0):
        log.finished_at = datetime.utcnow()
        log.status = status
        log.message = message
        log.records_synced = records
        db.session.commit()

    def _refresh(self):
        params = {
            'refresh_token': self.refresh_token,
            'client_id': self.cfg.CLIENT_ID,
            'client_secret': self.cfg.CLIENT_SECRET,
            'grant_type': 'refresh_token'
        }
        try:
            r = requests.post(self.token_url, params=params, timeout=15)
            print('[token_refresh] status', r.status_code)
            if r.status_code == 200:
                data = r.json()
                self.access_token = data.get('access_token', self.access_token)
                self.refresh_token = data.get('refresh_token', self.refresh_token)
                print('[token_refresh] success')
                return True
            else:
                print('[token_refresh] failed', r.text[:400])
        except Exception as e:
            print('[token_refresh] exception', e)
            traceback.print_exc()
        return False

    def _headers(self):
        if not self.access_token:
            self._refresh()
        return {
            'Authorization': f'Zoho-oauthtoken {self.access_token}',
            'Content-Type': 'application/json'
        }

    def _parse_datetime(self, dt_str):
        """Parse datetime string from Zoho API"""
        if not dt_str:
            return None
        try:
            return date_parser.parse(dt_str)
        except:
            try:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except:
                return None

    def _parse_date(self, date_str):
        """Parse date string from Zoho API"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    def _parse_int(self, value):
        """Safely parse integer"""
        if value is None or value == '':
            return None
        try:
            return int(value)
        except:
            return None

    def _parse_float(self, value):
        """Safely parse float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except:
            return None

    def _get_name_from_dict(self, field):
        """Extract name from dict field - returns string or None"""
        if field is None:
            return None
        if isinstance(field, dict):
            return field.get('name')
        if isinstance(field, str):
            return field
        return str(field) if field else None

    def _get_email_from_dict(self, field):
        """Extract email from dict field - returns string or None"""
        if isinstance(field, dict):
            return field.get('email')
        return None

    def _safe_str(self, value):
        """Safely convert any value to string or None"""
        if value is None or value == '':
            return None
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        if isinstance(value, dict):
            return value.get('name') or value.get('id') or str(value)
        if isinstance(value, list):
            return json.dumps(value)
        return str(value)

    def get_module_fields(self, module):
        """Get list of all field names for a module"""
        url = f"{self.base_url}/settings/fields"
        params = {'module': module}
        try:
            r = requests.get(url, params=params, headers=self._headers(), timeout=15)
            if r.status_code == 200:
                fields_data = r.json().get('fields', [])
                field_names = [f['api_name'] for f in fields_data]
                print(f'[get_module_fields] {module} has {len(field_names)} fields')
                return ','.join(field_names)
            else:
                print(f'[get_module_fields] failed for {module}: {r.status_code}')
                return None
        except Exception as e:
            print(f'[get_module_fields] exception for {module}:', e)
            return None

    def fetch_module(self, module):
        url = f"{self.base_url}/{module}"

        params = {
            'page': 1,
            'per_page': self.cfg.RECORDS_PER_PAGE
        }

        if module in ['Contacts', 'Accounts', 'Pipelines', 'Events', 'Tasks', 'Notes', 'Calls']:
            fields = self.get_module_fields(module)
            if fields:
                params['fields'] = fields
            else:
                print(f'[fetch_module] using fallback fields for {module}')
                params['fields'] = 'id,Created_Time,Modified_Time'

        results = []
        print(f'[fetch_module] start module={module} url={url}')

        while True:
            try:
                r = requests.get(url, params=params, headers=self._headers(), timeout=self.cfg.REQUEST_TIMEOUT)
            except Exception as e:
                print(f'[fetch_module] request exception for {module}:', e)
                traceback.print_exc()
                return results

            print(f'[fetch_module] module={module} page={params["page"]} status={r.status_code}')

            if r.status_code == 401:
                print('[fetch_module] got 401 - attempting token refresh')
                if not self._refresh():
                    print('[fetch_module] token refresh failed; aborting fetch')
                    return results
                continue

            if r.status_code != 200:
                print(f'[fetch_module] non-200 response: {r.status_code} body: {r.text[:500]}')
                return results

            try:
                j = r.json()
            except Exception as e:
                print('[fetch_module] json decode error', e)
                return results

            data = j.get('data', [])
            print(f'[fetch_module] got {len(data)} records on page {params["page"]}')

            results.extend(data)
            more = j.get('info', {}).get('more_records', False)
            if not more:
                break

            params['page'] += 1
            time.sleep(self.cfg.RATE_LIMIT_DELAY)

        print(f'[fetch_module] finished module={module} total={len(results)}')
        return results

    def sync_module_to_db(self, module, model):
        """
        Sync module data to database with UPSERT logic:
        - INSERT new records (zoho_id not found)
        - UPDATE existing records (zoho_id found) - ALWAYS UPDATE, never skip
        - DELETE records that no longer exist in Zoho
        """
        started = datetime.utcnow()
        log = self._log(module)

        try:
            data = self.fetch_module(module)
            print(f'[sync_module_to_db] fetched {len(data)} records for {module}')

            inserted_count = 0
            updated_count = 0

            # Build a dictionary of existing records by zoho_id for quick lookup
            existing_records = {rec.zoho_id: rec for rec in model.query.all()}
            print(f'[sync_module_to_db] found {len(existing_records)} existing records in DB')

            # Track which zoho_ids we've seen in this sync
            synced_zoho_ids = set()

            # Process each record from Zoho
            for idx, rec in enumerate(data):
                try:
                    zoho_id = self._safe_str(rec.get('id'))
                    if not zoho_id:
                        print(f'[sync_module_to_db] skipping record without zoho_id at index {idx}')
                        continue

                    synced_zoho_ids.add(zoho_id)

                    # Check if record exists
                    if zoho_id in existing_records:
                        row = existing_records[zoho_id]
                        is_update = True
                    else:
                        row = model()
                        is_update = False

                    # ALWAYS update the data - store full JSON
                    row.data = json.dumps(rec)

                    # Common fields for all modules
                    row.zoho_id = zoho_id
                    row.created_time = self._parse_datetime(rec.get('Created_Time'))
                    row.modified_time = self._parse_datetime(rec.get('Modified_Time'))

                    # Module-specific field mapping
                    if module == 'Contacts':
                        row.full_name = self._safe_str(rec.get('Full_Name'))
                        row.first_name = self._safe_str(rec.get('First_Name'))
                        row.last_name = self._safe_str(rec.get('Last_Name'))
                        row.email = self._safe_str(rec.get('Email'))
                        row.phone = self._safe_str(rec.get('Phone'))
                        row.mobile = self._safe_str(rec.get('Mobile'))
                        row.account_name = self._get_name_from_dict(rec.get('Account_Name'))
                        row.title = self._safe_str(rec.get('Title'))
                        row.department = self._safe_str(rec.get('Department'))
                        row.owner_name = self._get_name_from_dict(rec.get('Owner'))
                        row.owner_email = self._get_email_from_dict(rec.get('Owner'))
                        row.mailing_street = self._safe_str(rec.get('Mailing_Street'))
                        row.mailing_city = self._safe_str(rec.get('Mailing_City'))
                        row.mailing_state = self._safe_str(rec.get('Mailing_State'))
                        row.mailing_zip = self._safe_str(rec.get('Mailing_Zip'))
                        row.mailing_country = self._safe_str(rec.get('Mailing_Country'))
                        row.description = self._safe_str(rec.get('Description'))
                        row.lead_source = self._safe_str(rec.get('Lead_Source'))

                    elif module == 'Accounts':
                        row.account_name = self._safe_str(rec.get('Account_Name'))
                        row.firm_name = self._safe_str(rec.get('Firm_Name'))
                        row.phone = self._safe_str(rec.get('Phone'))
                        row.website = self._safe_str(rec.get('Website'))
                        row.owner_name = self._get_name_from_dict(rec.get('Owner'))
                        row.owner_email = self._get_email_from_dict(rec.get('Owner'))
                        row.billing_street = self._safe_str(rec.get('Billing_Street'))
                        row.billing_city = self._safe_str(rec.get('Billing_City'))
                        row.billing_state = self._safe_str(rec.get('Billing_State'))
                        row.billing_code = self._safe_str(rec.get('Billing_Code'))
                        row.billing_country = self._safe_str(rec.get('Billing_Country'))
                        row.line_of_business = self._safe_str(rec.get('Line_of_Business'))
                        row.no_of_branches = self._parse_int(rec.get('No_of_Branches'))
                        row.revenue_type = self._safe_str(rec.get('Revenue_Type'))
                        row.payment_terms = self._safe_str(rec.get('Payment_Terms'))
                        row.gstin_uin = self._safe_str(rec.get('GSTIN_UIN'))
                        row.expected_services_type = self._safe_str(rec.get('Expected_Services_Type'))
                        row.description = self._safe_str(rec.get('Description'))
                        row.last_activity_time = self._parse_datetime(rec.get('Last_Activity_Time'))

                    elif module == 'Pipelines':
                        row.deal_name = self._safe_str(rec.get('Deal_Name'))
                        row.account_name = self._get_name_from_dict(rec.get('Account_Name'))
                        row.contact_name = self._get_name_from_dict(rec.get('Contact_Name'))
                        row.stage = self._safe_str(rec.get('Stage'))
                        row.amount = self._parse_float(rec.get('Amount'))
                        row.closing_date = self._parse_date(rec.get('Closing_Date'))
                        row.pipeline = self._safe_str(rec.get('Pipeline'))
                        row.sub_pipeline = self._safe_str(rec.get('Sub_Pipeline'))
                        row.owner_name = self._get_name_from_dict(rec.get('Owner'))
                        row.owner_email = self._get_email_from_dict(rec.get('Owner'))
                        row.deal_type = self._safe_str(rec.get('Deal_Type'))
                        row.business_type = self._safe_str(rec.get('Business_Type'))
                        row.expected_services_type = self._safe_str(rec.get('Expected_Services_Type'))
                        row.lead_source = self._safe_str(rec.get('Lead_Source'))
                        row.lead_source_from = self._safe_str(rec.get('Lead_Source_From'))
                        row.lead_origin = self._safe_str(rec.get('Lead_Origin'))
                        row.probability = self._parse_float(rec.get('Probability'))
                        row.next_step = self._safe_str(rec.get('Next_Step'))
                        row.revenue_type = self._safe_str(rec.get('Revenue_Type'))
                        row.recurring_mode = self._safe_str(rec.get('Recurring_Mode'))
                        row.follow_up_date = self._parse_date(rec.get('Follow_up_Date'))
                        row.description = self._safe_str(rec.get('Description'))
                        row.last_activity_time = self._parse_datetime(rec.get('Last_Activity_Time'))

                    elif module == 'Calls':
                        row.subject = self._safe_str(rec.get('Subject'))
                        row.call_type = self._safe_str(rec.get('Call_Type'))
                        row.call_status = self._safe_str(rec.get('Call_Status'))
                        row.call_purpose = self._safe_str(rec.get('Call_Purpose'))
                        row.call_agenda = self._safe_str(rec.get('Call_Agenda'))
                        row.call_duration = self._safe_str(rec.get('Call_Duration'))

                        if rec.get('Call_Duration'):
                            try:
                                parts = str(rec.get('Call_Duration')).split(':')
                                row.call_duration_seconds = int(parts[0]) * 60 + (int(parts[1]) if len(parts) > 1 else 0)
                            except:
                                row.call_duration_seconds = None

                        row.call_start_time = self._parse_datetime(rec.get('Call_Start_Time'))
                        row.caller_id = self._safe_str(rec.get('Caller_ID'))
                        row.who_id_name = self._get_name_from_dict(rec.get('Who_Id'))
                        row.owner_name = self._get_name_from_dict(rec.get('Owner'))
                        row.owner_email = self._get_email_from_dict(rec.get('Owner'))
                        row.description = self._safe_str(rec.get('Description'))
                        row.voice_recording = self._safe_str(rec.get('Voice_Recording__s'))
                        row.reminder = self._safe_str(rec.get('Reminder'))

                    elif module == 'Events':
                        row.event_title = self._safe_str(rec.get('Event_Title'))
                        row.start_datetime = self._parse_datetime(rec.get('Start_DateTime'))
                        row.end_datetime = self._parse_datetime(rec.get('End_DateTime'))
                        row.all_day = rec.get('All_day', False)
                        row.venue = self._safe_str(rec.get('Venue'))
                        row.owner_name = self._get_name_from_dict(rec.get('Owner'))
                        row.owner_email = self._get_email_from_dict(rec.get('Owner'))
                        row.description = self._safe_str(rec.get('Description'))
                        participants = rec.get('Participants', [])
                        row.participants = json.dumps(participants) if participants else None
                        row.remind_at = self._parse_datetime(rec.get('Remind_At'))
                        row.check_in_time = self._parse_datetime(rec.get('Check_In_Time'))
                        row.check_out_time = self._parse_datetime(rec.get('RIQ_Check_out_Time'))
                        row.time_spent_mins = self._parse_int(rec.get('RIQ_Time_Spent_at_Location_mins'))
                        row.related_module = self._safe_str(rec.get('$related_module'))
                        row.booking_id = self._safe_str(rec.get('BookingId'))

                    elif module == 'Tasks':
                        row.subject = self._safe_str(rec.get('Subject'))
                        row.due_date = self._parse_date(rec.get('Due_Date'))
                        row.status = self._safe_str(rec.get('Status'))
                        row.priority = self._safe_str(rec.get('Priority'))
                        row.owner_name = self._get_name_from_dict(rec.get('Owner'))
                        row.owner_email = self._get_email_from_dict(rec.get('Owner'))
                        row.related_to_name = self._get_name_from_dict(rec.get('Related_To'))
                        row.related_to_module = self._safe_str(rec.get('$related_module'))
                        row.description = self._safe_str(rec.get('Description'))
                        row.remind_at = self._parse_datetime(rec.get('Remind_At'))

                    elif module == 'Notes':
                        row.note_title = self._safe_str(rec.get('Note_Title'))
                        row.note_content = self._safe_str(rec.get('Note_Content'))
                        row.owner_name = self._get_name_from_dict(rec.get('Owner'))
                        row.owner_email = self._get_email_from_dict(rec.get('Owner'))
                        row.parent_id_name = self._get_name_from_dict(rec.get('Parent_Id'))
                        row.parent_module = self._safe_str(rec.get('$se_module'))

                    # Add new records to session
                    if not is_update:
                        db.session.add(row)
                        inserted_count += 1
                    else:
                        updated_count += 1

                    # Commit in batches for better performance
                    if (idx + 1) % 100 == 0:
                        db.session.commit()
                        print(f'[sync_module_to_db] committed batch at record {idx + 1}/{len(data)}')

                except Exception as row_error:
                    print(f'[sync_module_to_db] Error processing record {idx + 1}/{len(data)} in {module}')
                    print(f'  Record ID: {rec.get("id")}')
                    print(f'  Error: {row_error}')
                    traceback.print_exc()
                    db.session.rollback()
                    continue

            # Final commit for remaining records
            db.session.commit()

            # Delete records that no longer exist in Zoho
            deleted_count = 0
            for zoho_id, existing_row in existing_records.items():
                if zoho_id not in synced_zoho_ids:
                    db.session.delete(existing_row)
                    deleted_count += 1

            if deleted_count > 0:
                db.session.commit()

            summary = f'Inserted: {inserted_count}, Updated: {updated_count}, Deleted: {deleted_count}'
            print(f'[sync_module_to_db] {module} - {summary}')

            self._finish(log, 'success', summary, inserted_count + updated_count)
            return True, summary

        except Exception as e:
            db.session.rollback()
            tb = traceback.format_exc()
            print('[sync_module_to_db] exception', e)
            print(tb)
            self._finish(log, 'failed', str(e))
            return False, str(e)

    def sync_all(self):
        """Sync all modules"""
        modules = [
            ('Contacts', Contact),
            ('Accounts', Account),
            ('Pipelines', Pipeline),
            ('Calls', Call),
            ('Events', Event),
            ('Tasks', Task),
            ('Notes', Note)
        ]
        results = {}

        for mod, model in modules:
            ok, msg = self.sync_module_to_db(mod, model)
            results[mod] = {'ok': ok, 'msg': msg}

        return results