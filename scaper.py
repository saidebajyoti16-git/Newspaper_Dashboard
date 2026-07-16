import os
import re
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3

# Suppress certificate warning logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NEWSPAPER_URLS = {
    "Times of India": "https://dailyepaper.in/times-of-india-epaper-pdf-free-download-2026/",
    "Live Mint": "https://dailyepaper.in/live-mint-epaper-feb-2026/",
    "Economic Times": "https://dailyepaper.in/economic-times-newspaper-today-2026/",
    "Hindustan Times": "https://dailyepaper.in/hindustan-times-epaper-download-2026/"
}

def extract_drive_id(text):
    """Helper to extract a Google Drive ID from a URL or text."""
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', text) or re.search(r'id=([a-zA-Z0-9_-]+)', text)
    if match:
        return match.group(1)
    return None

def resolve_download_link(target_link):
    """Bypasses tracking layers to isolate the direct underlying Drive ID."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    direct_id = extract_drive_id(target_link)
    if direct_id:
        return direct_id, "embed"
        
    try:
        sub_response = requests.get(target_link, headers=headers, verify=False, timeout=10)
        sub_soup = BeautifulSoup(sub_response.text, 'html.parser')
        
        for sub_link in sub_soup.find_all('a'):
            sub_href = sub_link.get('href', '')
            drive_id = extract_drive_id(sub_href)
            if drive_id:
                return drive_id, "embed"
                
        drive_id_fallback = extract_drive_id(sub_response.text)
        if drive_id_fallback:
            return drive_id_fallback, "embed"
            
    except Exception:
        pass
        
    return target_link, "external"

def extract_date_from_element(element):
    """Locates explicit publication dates near the target download anchor tag."""
    parent = element.find_parent(['tr', 'p', 'li', 'div'])
    text_to_search = parent.text if parent else element.text
    
    # Strict Regex: Matches "07 Jul 2026" or "7 July 2026" specifically requiring a textual month alpha sequence
    date_match = re.search(r'\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}', text_to_search)
    if date_match:
        return date_match.group(0)
        
    # Secondary fallback check requiring at least day + textual month abbreviation
    date_match_short = re.search(r'\d{1,2}\s+[A-Za-z]{3,9}', text_to_search)
    if date_match_short:
        return f"{date_match_short.group(0)} 2026"
        
    return None

def get_recent_papers(url, current_paper_name, max_days=5):
    """Scrapes content-scoped links while enforcing strict cross-paper exclusions."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    results = []
    
    # Identify names of OTHER newspapers to act as a blacklist filter
    all_papers = ["times of india", "live mint", "economic times", "hindustan times", "the hindu", "pioneer", "daily pioneer"]
    blacklist_papers = [p for p in all_papers if p != current_paper_name.lower()]
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the main entry container strictly
        main_content = soup.find(['div', 'article', 'main'], class_=['entry-content', 'post-content', 'single-post']) or soup
        links = main_content.find_all('a')
        
        count = 0
        for link in links:
            text = link.text.strip().lower()
            href = link.get('href', '').lower()
            
            # Skip link entirely if it explicitly names a competitor or promotional paper link
            if any(bad_word in text or bad_word in href for bad_word in blacklist_papers):
                continue
                
            if "download" in text or "download" in href:
                if any(k in href for k in ["dailyepaper.in", "drive.google.com", "go.", "drive"]):
                    date_label = extract_date_from_element(link)
                    
                    # If date doesn't match standard clean formats, bypass it
                    if not date_label or "am" in date_label.lower() or "pm" in date_label.lower():
                        continue
                        
                    link_data, link_type = resolve_download_link(link.get('href'))
                    
                    if link_data and not any(r['date'] == date_label for r in results):
                        results.append({
                            "date": date_label,
                            "data": link_data,
                            "type": link_type
                        })
                        count += 1
                        
                if count >= max_days:
                    break
                    
    except Exception as e:
        print(f"  -> Error parsing content layout: {e}")
        
    return results

def generate_professional_dashboard(newspaper_data):
    """Generates the responsive web application template utilizing Tailwind CSS."""
    today_str = datetime.now().strftime("%B %d, %Y")
    json_data = json.dumps(newspaper_data)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ProNews | Daily ePaper Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: #f1f1f1; }}
            ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}
        </style>
    </head>
    <body class="bg-slate-50 text-slate-800 h-screen flex overflow-hidden font-sans">

        <aside class="w-72 bg-white border-r border-slate-200 flex flex-col h-full shadow-sm z-10">
            <div class="p-6 border-b border-slate-100">
                <h1 class="text-2xl font-bold text-blue-700 tracking-tight flex items-center gap-2">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5L18.5 7H20"></path></svg>
                    ProNews
                </h1>
                <p class="text-xs text-slate-500 mt-1 font-medium tracking-wide uppercase">Automated Feed • {today_str}</p>
            </div>
            
            <div class="flex-1 overflow-y-auto p-4 space-y-2" id="paper-list"></div>
            
            <div class="p-4 border-t border-slate-100 text-xs text-slate-400 text-center">
                Refreshed dynamically from source.
            </div>
        </aside>

        <main class="flex-1 flex flex-col h-full relative bg-slate-50">
            <header class="bg-white px-8 py-5 border-b border-slate-200 flex justify-between items-center shadow-sm z-10">
                <div>
                    <h2 id="current-paper-title" class="text-xl font-bold text-slate-800">Select a Newspaper</h2>
                    <p id="current-paper-subtitle" class="text-sm text-slate-500">Select an option from the sidebar to begin reading.</p>
                </div>
                
                <div class="flex items-center gap-3">
                    <label for="date-selector" class="text-sm font-medium text-slate-600">Edition Date:</label>
                    <select id="date-selector" class="bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-48 p-2.5 shadow-sm outline-none cursor-pointer" disabled>
                        <option>No data loaded</option>
                    </select>
                </div>
            </header>

            <div class="flex-1 p-6 overflow-hidden flex flex-col">
                <div id="viewer-container" class="flex-1 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex items-center justify-center relative">
                    <div class="text-slate-400 flex flex-col items-center gap-3">
                        <svg class="w-12 h-12 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                        <p class="font-medium">Viewer Area</p>
                    </div>
                </div>
            </div>
        </main>

        <script>
            const db = {json_data};
            let currentPaper = null;

            const paperListEl = document.getElementById('paper-list');
            const titleEl = document.getElementById('current-paper-title');
            const subtitleEl = document.getElementById('current-paper-subtitle');
            const dateSelectorEl = document.getElementById('date-selector');
            const viewerContainerEl = document.getElementById('viewer-container');

            Object.keys(db).forEach(paperName => {{
                const btn = document.createElement('button');
                btn.className = 'w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors duration-200 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-transparent hover:border-blue-100 flex justify-between items-center group';
                btn.innerHTML = `
                    ${{paperName}}
                    <svg class="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                `;
                btn.onclick = () => loadPaper(paperName, btn);
                paperListEl.appendChild(btn);
            }});

            function loadPaper(paperName, activeBtn) {{
                currentPaper = paperName;
                
                document.querySelectorAll('#paper-list button').forEach(b => {{
                    b.classList.remove('bg-blue-50', 'text-blue-700', 'border-blue-100');
                    b.querySelector('svg').classList.remove('opacity-100');
                }});
                activeBtn.classList.add('bg-blue-50', 'text-blue-700', 'border-blue-100');
                activeBtn.querySelector('svg').classList.add('opacity-100');

                titleEl.textContent = paperName;
                subtitleEl.textContent = "Verified archival editions available below.";

                const editions = db[paperName];
                
                if (!editions || editions.length === 0) {{
                    dateSelectorEl.innerHTML = '<option>No verified dates found</option>';
                    dateSelectorEl.disabled = true;
                    showError("No explicitly dated editions have been scraped yet.");
                    return;
                }}

                dateSelectorEl.disabled = false;
                dateSelectorEl.innerHTML = '';
                editions.forEach((edition, index) => {{
                    const opt = document.createElement('option');
                    opt.value = index;
                    opt.textContent = edition.date;
                    dateSelectorEl.appendChild(opt);
                }});

                renderViewer(editions[0]);
            }}

            dateSelectorEl.addEventListener('change', (e) => {{
                if(currentPaper && db[currentPaper]) {{
                    const selectedIndex = e.target.value;
                    renderViewer(db[currentPaper][selectedIndex]);
                }}
            }});

            function renderViewer(editionData) {{
                if (editionData.type === 'embed') {{
                    const url = `https://drive.google.com/file/d/${{editionData.data}}/preview`;
                    viewerContainerEl.innerHTML = `<iframe src="${{url}}" allow="autoplay" class="w-full h-full border-0 absolute inset-0 rounded-xl"></iframe>`;
                }} else if (editionData.type === 'external') {{
                    viewerContainerEl.innerHTML = `
                        <div class="text-center p-8">
                            <div class="bg-blue-50 text-blue-600 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                            </div>
                            <h3 class="text-lg font-bold text-slate-800 mb-2">External Link Required</h3>
                            <p class="text-slate-500 mb-6 max-w-md mx-auto">This specific edition requires you to pass through a protective gateway before viewing. Click below to open it safely.</p>
                            <a href="${{editionData.data}}" target="_blank" class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
                                Access Edition Source
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                            </a>
                        </div>
                    `;
                }}
            }}

            function showError(msg) {{
                viewerContainerEl.innerHTML = `
                    <div class="text-center text-red-500 p-8 bg-red-50 rounded-lg">
                        <svg class="w-12 h-12 mx-auto mb-3 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        <p class="font-semibold">${{msg}}</p>
                    </div>
                `;
            }}
        </script>
    </body>
    </html>
    """

    with open("newspaper_dashboard.html", "w", encoding="utf-8") as file:
        file.write(html_content)
    print("\n[SUCCESS] ProNews Dashboard updated! Open 'newspaper_dashboard.html' to view.")

def main():
    print("====================================")
    print(" Starting Core Filtering Protocol...")
    print("====================================\n")
    
    newspaper_data = {}
    
    for name, url in NEWSPAPER_URLS.items():
        print(f"Scraping valid clean entries for: {name}...")
        editions = get_recent_papers(url, name, max_days=5)
        newspaper_data[name] = editions
        print(f"  -> Successfully isolated {len(editions)} matching dates.\n")
        
    print("Compiling professional web interface...")
    generate_professional_dashboard(newspaper_data)

if __name__ == '__main__':
    main()