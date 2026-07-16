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
    "Hindustan Times": "https://dailyepaper.in/hindustan-times-epaper-download-2026/",
    "Business Line":"https://www.careerswave.in/business-line-epaper-pdf-free-download/"
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
    
    date_match = re.search(r'\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}', text_to_search)
    if date_match:
        return date_match.group(0)
        
    date_match_short = re.search(r'\d{1,2}\s+[A-Za-z]{3,9}', text_to_search)
    if date_match_short:
        return f"{date_match_short.group(0)} 2026"
        
    return None

def get_recent_papers(url, current_paper_name, max_days=5):
    """Scrapes content-scoped links while enforcing strict cross-paper exclusions."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    results = []
    
    all_papers = ["times of india", "live mint", "economic times", "hindustan times", "the hindu", "pioneer", "daily pioneer"]
    blacklist_papers = [p for p in all_papers if p != current_paper_name.lower()]
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        main_content = soup.find(['div', 'article', 'main'], class_=['entry-content', 'post-content', 'single-post']) or soup
        links = main_content.find_all('a')
        
        count = 0
        for link in links:
            text = link.text.strip().lower()
            href = link.get('href', '').lower()
            
            if any(bad_word in text or bad_word in href for bad_word in blacklist_papers):
                continue
                
            if "download" in text or "download" in href:
                if any(k in href for k in ["dailyepaper.in", "drive.google.com", "go.", "drive"]):
                    date_label = extract_date_from_element(link)
                    
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
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; }}
            ::-webkit-scrollbar {{ width: 6px; }}
            ::-webkit-scrollbar-track {{ background: transparent; }}
            ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 10px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}
            
            /* Ensure iframe background is white during fullscreen */
            #viewer-container:fullscreen {{ background-color: white; padding: 0; border-radius: 0; }}
            #viewer-container:-webkit-full-screen {{ background-color: white; padding: 0; border-radius: 0; }}
            #viewer-container:-ms-fullscreen {{ background-color: white; padding: 0; border-radius: 0; }}
        </style>
    </head>
    <body class="bg-slate-50 text-slate-800 h-screen flex overflow-hidden">

        <aside class="w-72 bg-white border-r border-slate-200 flex flex-col h-full shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-20">
            <div class="p-6 border-b border-slate-100 bg-gradient-to-b from-slate-50 to-white">
                <h1 class="text-2xl font-bold text-indigo-700 tracking-tight flex items-center gap-2.5">
                    <div class="bg-indigo-100 p-1.5 rounded-lg text-indigo-600">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5L18.5 7H20"></path></svg>
                    </div>
                    ProNews
                </h1>
                <p class="text-[11px] text-slate-400 mt-2 font-semibold tracking-wider uppercase">Automated Feed • {today_str}</p>
            </div>
            
            <div class="flex-1 overflow-y-auto p-4 space-y-1.5" id="paper-list"></div>
            
            <div class="p-4 border-t border-slate-100 bg-slate-50 text-[11px] text-slate-400 text-center font-medium">
                Data refreshed dynamically
            </div>
        </aside>

        <main class="flex-1 flex flex-col h-full relative bg-slate-50/50">
            <header class="bg-white px-8 py-5 border-b border-slate-200 flex justify-between items-center shadow-sm z-10">
                <div>
                    <h2 id="current-paper-title" class="text-xl font-bold text-slate-800 tracking-tight">Select a Newspaper</h2>
                    <p id="current-paper-subtitle" class="text-sm text-slate-500 mt-0.5">Select an option from the sidebar to begin reading.</p>
                </div>
                
                <div class="flex items-center gap-4">
                    <div id="date-selector-container" class="flex items-center gap-3 transition-opacity duration-300">
                        <label for="date-selector" class="text-sm font-semibold text-slate-500">Edition Date</label>
                        <div class="relative">
                            <select id="date-selector" class="appearance-none bg-slate-50 border border-slate-200 text-slate-700 text-sm font-medium rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 block w-48 py-2.5 pl-4 pr-10 shadow-sm outline-none cursor-pointer transition-all" disabled>
                                <option>No data loaded</option>
                            </select>
                            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                        </div>
                    </div>
                    
                    <button id="fullscreen-btn" onclick="toggleFullScreen()" class="hidden bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 shadow-sm focus:ring-2 focus:ring-slate-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
                        Full Screen
                    </button>
                </div>
            </header>

            <div class="flex-1 p-6 overflow-hidden flex flex-col">
                <div id="viewer-container" class="flex-1 bg-white rounded-2xl shadow-sm border border-slate-200/60 overflow-hidden flex items-center justify-center relative">
                    <div class="text-slate-300 flex flex-col items-center gap-4">
                        <div class="bg-slate-50 p-4 rounded-full">
                            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                        </div>
                        <p class="font-medium text-slate-400">Viewer Area</p>
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
            const dateSelectorContainer = document.getElementById('date-selector-container');
            const dateSelectorEl = document.getElementById('date-selector');
            const viewerContainerEl = document.getElementById('viewer-container');
            const fullscreenBtn = document.getElementById('fullscreen-btn');

            Object.keys(db).forEach(paperName => {{
                const btn = document.createElement('button');
                btn.className = 'w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 hover:bg-indigo-50 text-slate-600 hover:text-indigo-700 border border-transparent flex justify-between items-center group';
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
                    b.classList.remove('bg-indigo-50', 'text-indigo-700', 'shadow-sm', 'border-indigo-100/50');
                    b.classList.add('text-slate-600');
                    b.querySelector('svg').classList.remove('opacity-100');
                }});
                activeBtn.classList.remove('text-slate-600');
                activeBtn.classList.add('bg-indigo-50', 'text-indigo-700', 'shadow-sm', 'border-indigo-100/50');
                activeBtn.querySelector('svg').classList.add('opacity-100');

                titleEl.textContent = paperName;

                if (paperName === "The Hindu") {{
                    dateSelectorContainer.style.display = 'none';
                    subtitleEl.textContent = "Latest edition for today.";
                }} else {{
                    dateSelectorContainer.style.display = 'flex';
                    subtitleEl.textContent = "Verified archival editions available below.";
                }}

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
                // Show fullscreen button if it's an embed
                if (editionData.type === 'embed' || editionData.type === 'raw_embed') {{
                    fullscreenBtn.classList.remove('hidden');
                }} else {{
                    fullscreenBtn.classList.add('hidden');
                }}

                if (editionData.type === 'embed') {{
                    const url = `https://drive.google.com/file/d/${{editionData.data}}/preview`;
                    viewerContainerEl.innerHTML = `<iframe src="${{url}}" allow="autoplay" class="w-full h-full border-0 absolute inset-0 rounded-2xl" allowfullscreen></iframe>`;
                }} else if (editionData.type === 'raw_embed') {{
                     // Rendering Direct URL in iframe
                     viewerContainerEl.innerHTML = `<iframe src="${{editionData.data}}" class="w-full h-full border-0 absolute inset-0 rounded-2xl" allowfullscreen></iframe>`;
                }} else if (editionData.type === 'external') {{
                    viewerContainerEl.innerHTML = `
                        <div class="text-center p-8">
                            <div class="bg-indigo-50 text-indigo-600 rounded-2xl w-20 h-20 flex items-center justify-center mx-auto mb-5 shadow-sm">
                                <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                            </div>
                            <h3 class="text-xl font-bold text-slate-800 mb-2">Ready for Download</h3>
                            <p class="text-slate-500 mb-8 max-w-sm mx-auto leading-relaxed">This edition is hosted on an external secure server. Click below to view or download the PDF.</p>
                            <a href="${{editionData.data}}" target="_blank" class="inline-flex items-center gap-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3.5 px-7 rounded-xl transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5">
                                Access Today's Edition
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                            </a>
                        </div>
                    `;
                }}
            }}

            function toggleFullScreen() {{
                if (!document.fullscreenElement &&    // alternative standard method
                    !document.mozFullScreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement ) {{  // current working methods
                    if (viewerContainerEl.requestFullscreen) {{
                        viewerContainerEl.requestFullscreen();
                    }} else if (viewerContainerEl.msRequestFullscreen) {{
                        viewerContainerEl.msRequestFullscreen();
                    }} else if (viewerContainerEl.mozRequestFullScreen) {{
                        viewerContainerEl.mozRequestFullScreen();
                    }} else if (viewerContainerEl.webkitRequestFullscreen) {{
                        viewerContainerEl.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
                    }}
                }} else {{
                    if (document.exitFullscreen) {{
                        document.exitFullscreen();
                    }} else if (document.msExitFullscreen) {{
                        document.msExitFullscreen();
                    }} else if (document.mozCancelFullScreen) {{
                        document.mozCancelFullScreen();
                    }} else if (document.webkitExitFullscreen) {{
                        document.webkitExitFullscreen();
                    }}
                }}
            }}

            function showError(msg) {{
                viewerContainerEl.innerHTML = `
                    <div class="text-center text-rose-500 p-8 bg-rose-50 rounded-2xl border border-rose-100 max-w-md">
                        <svg class="w-12 h-12 mx-auto mb-4 opacity-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        <p class="font-semibold">${{msg}}</p>
                    </div>
                `;
            }}
        </script>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as file:
        file.write(html_content)
    print("\n[SUCCESS] ProNews Dashboard updated! Open 'index.html' to view.")


def main():
    print("====================================")
    print(" Starting Core Filtering Protocol...")
    print("====================================\n")
    
    newspaper_data = {}
    
    # 1. Dynamically Generate The Hindu Link for Today
    today_url_date = datetime.now().strftime("%d~%m~%Y")
    today_display_date = datetime.now().strftime("%B %d, %Y")
    
    # URL structure requested: uploads%2FTHE+HINDU+HD+Delhi+Editable+Full+Edition+DD~MM~YYYY.pdf
    hindu_dynamic_url = f"https://www.indiags.com/newspaper/pdf.php?file=uploads%2FTHE+HINDU+HD+Delhi+Editable+Full+Edition+{today_url_date}.pdf"
    
    print("Injecting dynamic URL for: The Hindu...")
    newspaper_data["The Hindu"] = [{
        "date": today_display_date,
        "data": hindu_dynamic_url,
        "type": "raw_embed" # CHANGED from "external" to force inline iframe display
    }]
    print("  -> Successfully injected today's edition.\n")
    
    # 2. Scrape the rest of the newspapers dynamically
    for name, url in NEWSPAPER_URLS.items():
        print(f"Scraping valid clean entries for: {name}...")
        editions = get_recent_papers(url, name, max_days=5)
        newspaper_data[name] = editions
        print(f"  -> Successfully isolated {len(editions)} matching dates.\n")
        
    print("Compiling professional web interface...")
    generate_professional_dashboard(newspaper_data)

if __name__ == '__main__':
    main()