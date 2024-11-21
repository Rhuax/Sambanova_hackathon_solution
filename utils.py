import re
import json
from graphviz import Digraph
from gantt_generator import generate_gantt_chart
from scrapy.selector import Selector
from excel_generator import generate_gantt_excel
import logging
from scrapy.crawler import CrawlerProcess
from urllib.parse import quote
import asyncio
from scrapy import signals
from scrapy.signalmanager import dispatcher
import random
import sys
from datetime import datetime
import os
import time
# Disable all existing loggers
"""for logger_name in logging.root.manager.loggerDict:
    logging.getLogger(logger_name).disabled = True"""

# Configure our logger only
logger = logging.getLogger(__name__)
logger.disabled = False
logger.setLevel(logging.INFO)

"""# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)"""

# Add our custom handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(message)s'))  # Simplified format
logger.addHandler(handler)

# Ensure no propagation to root logger
#logger.propagate = False

# Completely suppress Scrapy's logging
logging.getLogger('scrapy').setLevel(logging.ERROR)
logging.getLogger('twisted').setLevel(logging.ERROR)
logging.getLogger('filelock').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)

# Add a handler to our logger to ensure our messages get through
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(handler)

# Add random user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/91.0.864.59',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

def process_wbs(wbs_text: str) -> str:
    """
    Extracts the content between <wbs> tags from the text
    
    Args:
        wbs_text (str): The text containing the WBS enclosed in <wbs> tags
        
    Returns:
        str: The extracted WBS content, or empty string if no WBS tags found
    """
    # Use regex to find content between <wbs> tags
    wbs_pattern = r'<wbs>(.*?)</wbs>'
    wbs = re.search(wbs_pattern, wbs_text, re.DOTALL)
    
    if wbs:
        wbs = wbs.group(1).strip()
    else:
        wbs = ""
    function_pattern = r'<function_call>(.*?)</function_call>'
    function_call = re.search(function_pattern, wbs_text, re.DOTALL)
    if function_call:
        function_call = function_call.group(1).strip()
        function_call = json.loads(function_call)
    else:
        function_call = None
    return wbs, function_call
def process_gantt(gantt_text: str):
    """
    Extracts the gantt chart content and processes any function calls
    
    Args:
        gantt_text (str): The text containing the gantt chart data and potential function calls
        
    Returns:
        tuple: Tuple containing (list of tasks, plotly chart filename, excel filename)
    """    
    if "<function_call>" in gantt_text and "</function_call>" not in gantt_text:
        gantt_text += "</function_call>"
    # Extract function calls
    function_pattern = r'<function_call>(.*?)</function_call>'
    function_call = re.search(function_pattern, gantt_text, re.DOTALL)
    tasks = []
    plotly_filename = None
    excel_filename = None
    
    if function_call:
        function_call = json.loads(function_call.group(1).strip())
        function_call = function_call[0]
        if function_call["name"] == "create_gantt_chart_to_file":
            if "gantt_chart" in function_call["parameters"]:
                    tasks = function_call["parameters"]["gantt_chart"]["tasks"]
                    plotly_filename = f"gantt_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    excel_filename = f"gantt_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    logger.info(f"🎨 Creating Gantt chart")
                    generate_gantt_chart(tasks)
                    logger.info(f"🎨 Creating Excel file")
                    generate_gantt_excel(tasks, excel_filename)
    
    return tasks, plotly_filename, excel_filename
def wrap_text(text: str, width: int = 20) -> str:
    """
    Wraps text to specified width and joins with newlines
    
    Args:
        text (str): Text to wrap
        width (int): Maximum line length
        
    Returns:
        str: Wrapped text with newlines
    """
    # Split text into words and rejoin with newlines
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def generate_dependency_graph(nodes: list, edges: list) -> str:
    """
    Creates a clear and readable dependency graph with high resolution
    
    Args:
        nodes (list): List of node dictionaries with 'id' and 'label' keys
        edges (list): List of edge dictionaries with 'from' and 'to' keys
        
    Returns:
        str: Path to the generated graph image file
    """
    # Create a unique filename using timestamp
    output_file_filename = f"dependency_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    # Create a new directed graph
    dot = Digraph(comment='Dependency Graph')
    dot.attr(rankdir='LR')  # Left to right layout
    dot.attr('node', shape='box', style='rounded')
    
    # Set graph attributes for better readability
    dot.attr(
        bgcolor='white',
        size='8,8',
        dpi='300',
        fontname='Arial',
        fontsize='12'
    )
    
    # Add nodes
    for node in nodes:
        # Wrap long labels for better readability
        wrapped_label = wrap_text(node, width=20)
        dot.node(str(node), wrapped_label)
    
    # Add edges
    for edge in edges:
        dot.edge(str(edge[0]), str(edge[1]))
    
    # Render the graph to a file
    dot.render(output_file_filename.replace('.png', ''), format='png', cleanup=True)
    
    logger.info(f"📊 Generated dependency graph: {output_file_filename}")
    
    return output_file_filename
def process_team_structure(team_structure_text: str):
    """
    Extracts the team structure from the text and formats it in markdown
    """
    team_structure_pattern = r'<team>(.*?)</team>'
    team_structure = re.search(team_structure_pattern, team_structure_text, re.DOTALL)
    team_structure = json.loads(team_structure.group(1).strip())
    
    final_response = "## Team Structure\n\n"
    for i, (role, details) in enumerate(team_structure.items(), 1):
        final_response += f"### {i}. {role}\n"
        for detail, value in details.items():
            # Format each detail as a bullet point
            final_response += f"- **{detail}:** {value}\n"
        final_response += "\n"
        
    return final_response, team_structure

import scrapy


class SalarySpider(scrapy.Spider):
    name = "salary"
    custom_settings = {
        'CONCURRENT_REQUESTS': 5,          # Increased but still moderate
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        'DOWNLOAD_DELAY': 0.25,              # Reduced delay but not too aggressive
        'COOKIES_ENABLED': False,
        'RETRY_TIMES': 3,                 # Reduced retry times for faster failure
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403],
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_TIMEOUT': 30,           # Reduced timeout
    }
    
    def __init__(self, *args, **kwargs):
        self.start_urls = kwargs.pop('url_list', [])
        self.salary = None
        self.role = kwargs.pop('role', 'Unknown')
        super(SalarySpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        for url in self.start_urls:
            logger.info(f"🔍 Starting request for {self.role}")
            sys.stdout.flush()
            
            # Rotate between different user agents
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            
            # Add random delay between requests
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers=headers,
                meta={
                    'dont_redirect': True,
                    'handle_httpstatus_list': [302, 403, 429],
                    'download_timeout': 60,
                    'max_retry_times': 5,
                    'dont_merge_cookies': False
                },
                errback=self.handle_error,
                dont_filter=True,
                cb_kwargs={'attempt': 1}
            )

    def parse(self, response, attempt=1):
        if response.status in [403, 429]:
            if attempt <= 5:  # Try up to 5 times
                logger.warning(f"⚠️ Rate limited for {self.role} (attempt {attempt}/5)")
                delay = attempt * 5  # Increase delay with each attempt
                return scrapy.Request(
                    url=response.url,
                    callback=self.parse,
                    headers={'User-Agent': random.choice(USER_AGENTS)},
                    dont_filter=True,
                    meta=response.meta,
                    cb_kwargs={'attempt': attempt + 1},
                    errback=self.handle_error,
                    priority=10,
                    dont_merge_cookies=False
                )
            else:
                logger.error(f"❌ Max retries reached for {self.role}")
                self.salary = f"Unable to fetch salary for {self.role} (rate limited)"
                return
            
        logger.info(f"📝 Parsing search for {self.role}")
        sys.stdout.flush()
        
        try:
            
            follow_url = response.xpath('//div[@class="margin-bottom10 font-semibold sal-jobtitle"]/a/@href').get()
            
            if follow_url:
                logger.info(f"🔗 Found details link for {self.role}")
                sys.stdout.flush()
                
                # Add random delay before following
                
                
                headers = {
                    'User-Agent': random.choice(USER_AGENTS),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                }
                
                yield response.follow(
                    follow_url,
                    callback=self.parse2,
                    headers=headers,
                    meta={
                        'dont_redirect': True,
                        'handle_httpstatus_list': [302, 403, 429],
                        'download_timeout': 60
                    },
                    errback=self.handle_error,
                    dont_filter=True
                )
            else:
                self.salary = f"No salary data found for {self.role}"
                logger.error(f"❌ No details link found for {self.role}")
                sys.stdout.flush()
        except Exception as e:
            logger.error(f"❌ Error parsing search for {self.role}: {str(e)}")
            self.salary = f"Error fetching salary for {self.role}"

    def parse2(self, response):
        if response.status in [403, 429]:
            logger.error(f"⚠️ Access denied for {self.role} details (status: {response.status})")
            sys.stdout.flush()
            self.salary = f"Unable to fetch salary for {self.role} (access denied)"
            return
            
        logger.info(f"💰 Parsing salary for {self.role}")
        sys.stdout.flush()
        
        try:
            self.salary = response.xpath('//text[@id="top_salary_value"]/tspan/text()').get()
            
            if not self.salary:
                # Try alternative selectors if the first one fails
                self.salary = response.xpath('//div[contains(@class, "salary-value")]/text()').get()
                
            if self.salary:
                logger.info(f"✅ Found salary for {self.role}: {self.salary}")
            else:
                logger.error(f"❌ No salary found for {self.role}")
                self.salary = f"No salary data found for {self.role}"
        except Exception as e:
            logger.error(f"❌ Error parsing salary for {self.role}: {str(e)}")
            self.salary = f"Error fetching salary for {self.role}"
        
        sys.stdout.flush()

    def handle_error(self, failure):
        logger.error(f"❌ Request failed for {self.role}: {failure.value}")
        sys.stdout.flush()
        self.salary = f"Failed to fetch salary for {self.role}"

# Add this at the module level (outside any function)
def run_spider_process(function_call, roles, results_dict, completed_roles, total_roles):
    from scrapy.crawler import CrawlerRunner
    from twisted.internet import reactor
    from twisted.internet.defer import DeferredList
    
    def spider_closed(spider):
        if isinstance(spider, SalarySpider):
            results_dict[spider.role] = spider.salary
            completed_roles.value += 1
            progress = (completed_roles.value / total_roles) * 100
            logger.info(f"✅ [{progress:.1f}%] Completed {spider.role}: {spider.salary}")
            sys.stdout.flush()
    
    # Create a CrawlerRunner instance with telnet console disabled
    runner = CrawlerRunner({
        'USER_AGENT': random.choice(USER_AGENTS),
        'LOG_LEVEL': 'INFO',
        'LOG_ENABLED': True,
        'DOWNLOAD_TIMEOUT': 30,
        'CONCURRENT_REQUESTS': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        'DOWNLOAD_DELAY': 0.25,
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403],
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_FAIL_ON_DATALOSS': False,
        'TELNETCONSOLE_ENABLED': False,
        'TELNETCONSOLE_PORT': None,
        'EXTENSIONS': {
            'scrapy.extensions.telnet.TelnetConsole': None
        }
    })
    
    # Setup spiders
    deferreds = []
    for call in function_call:
        if call["name"] == "get_role_average_salary":
            role = call['parameters']['role']
            roles.append(role)
            
            encoded_role = quote(role)
            url = f"https://www.salary.com/tools/salary-calculator/search?keyword={encoded_role}&location="
            
            # Connect spider_closed signal
            dispatcher.connect(spider_closed, signal=signals.spider_closed)
            
            # Schedule spider
            deferred = runner.crawl(SalarySpider, url_list=[url], role=role)
            deferreds.append(deferred)
    
    # Create a deferred list
    defer_list = DeferredList(deferreds, consumeErrors=True)
    
    # Add callback to stop reactor
    def stop_reactor(null):
        if reactor.running:
            reactor.stop()
    
    defer_list.addCallback(stop_reactor)
    
    # Start the reactor
    if not reactor.running:
        reactor.run()

async def process_estimate(estimate: str) ->str:
    """
    Processes the estimate to return a list of salaries in the same order as the input roles
    """
    logger.info("🚀 Starting salary fetching process")
    sys.stdout.flush()
    
    function_pattern = r'<function_call>(.*?)</function_call>'
    function_call = re.search(function_pattern, estimate, re.DOTALL)
    results = []
    
    if function_call:
        function_call = json.loads(function_call.group(1).strip())
        roles = []
        
        # Use Manager for shared objects between processes
        from multiprocessing import Manager, Value
        
        with Manager() as manager:
            results_dict = manager.dict()
            completed_roles = Value('i', 0)
            total_roles = len([call for call in function_call if call["name"] == "get_role_average_salary"])
            
            try:
                import multiprocessing
                
                # Run the spider in a separate process
                process = multiprocessing.Process(
                    target=run_spider_process,
                    args=(function_call, roles, results_dict, completed_roles, total_roles)
                )
                process.start()
                
                # Wait for the process to complete
                while completed_roles.value < total_roles:
                    await asyncio.sleep(0.1)
                
                # Create ordered results list
                results = [f"{role}: {results_dict.get(role, 'Not found')}" for role in roles]
                logger.info("✨ Salary fetching completed!")
                sys.stdout.flush()
                
                # Terminate and clean up the process
                process.terminate()
                process.join()
                
            except Exception as e:
                logger.error(f"Error during crawling: {str(e)}")
                results = [f"{role}: Error fetching salary" for role in roles]
            
    return ' '.join(results)

if __name__ == "__main__":
    
    get_salary_from_role("software engineer")
    
