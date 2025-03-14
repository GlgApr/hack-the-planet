# @title Subdomain Finder
# @markdown Use: python subfin.py <domain> <wordlist> <output> <threads> <timeout>
# @Galang Aprilian - 2025
import dns.resolver
import requests
import argparse
import concurrent.futures
import re
import os
import time
import random
from datetime import datetime

class SubdomainFinder:
    def __init__(self, domain, wordlist=None, output=None, threads=10, timeout=5):
        self.domain = domain
        self.wordlist_file = wordlist
        self.output_file = output if output else f"{domain}_subdomains_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.threads = threads
        self.timeout = timeout
        self.subdomains = set()
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 1
        self.resolver.lifetime = 1
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
    def get_random_user_agent(self):
        return random.choice(self.user_agents)
        
    def load_wordlist(self):
        if not self.wordlist_file:
            # Default small wordlist for common subdomains
            return [
                'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk',
                'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'admin', 'test', 'mx', 
                'portal', 'blog', 'dev', 'api', 'cloud', 'vpn', 'secure', 'server', 'mobile',
                'docs', 'shop', 'forum', 'login', 'app', 'cdn', 'stage', 'beta', 'pay', 'owa',
                'dashboard', 'images', 'support', 'git', 'gitlab', 'jenkins', 'intranet',
                'media', 'store', 'web', 'panel', 'wiki', 'help', 'moodle', 'status', 'crm',
                'student', 'alumni', 'library', 'elearning', 'e-learning', 'sso', 'research',
                'mail2', 'remote', 'db', 'database', 'apps', 'calendar', 'chat', 'citrix',
                'connect', 'data', 'demo', 'directory', 'dl', 'dns', 'host', 'hr', 'jobs',
                'learn', 'lms', 'local', 'm', 'manage', 'mgmt', 'monitor', 'new', 'news',
                'old', 'online', 'partners', 'pma', 'prod', 'project', 'proxy', 'ra',
                'remove', 'reports', 'sandbox', 'search', 'services', 'share', 'staff',
                'study', 'training', 'uat', 'upload', 'video', 'videos', 'workspace', 'www2'
            ]
        else:
            try:
                with open(self.wordlist_file, 'r') as f:
                    return [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"Error loading wordlist: {e}")
                return []
                
    def dns_brute_force(self, subdomain):
        full_domain = f"{subdomain}.{self.domain}"
        try:
            self.resolver.resolve(full_domain, 'A')
            self.subdomains.add(full_domain)
            print(f"[+] Discovered subdomain: {full_domain}")
            return full_domain
        except:
            return None
    
    def crt_sh_search(self):
        print("\n[*] Searching crt.sh for SSL certificates...")
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(
                f"https://crt.sh/?q=%.{self.domain}&output=json", 
                headers=headers,
                timeout=self.timeout
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    for entry in data:
                        name_value = entry.get('name_value', '')
                        if name_value:
                            # Extract subdomains using regex
                            subdomains = re.findall(r'([a-zA-Z0-9._-]+\.' + re.escape(self.domain) + ')', name_value)
                            for subdomain in subdomains:
                                if subdomain not in self.subdomains and subdomain != self.domain:
                                    self.subdomains.add(subdomain)
                                    print(f"[+] Discovered from crt.sh: {subdomain}")
                except Exception as e:
                    print(f"[-] Error parsing crt.sh response: {e}")
        except Exception as e:
            print(f"[-] Error searching crt.sh: {e}")
            print("[*] Trying alternative crt.sh query method...")
            try:
                # Alternative method with text search
                response = requests.get(
                    f"https://crt.sh/?q=%.{self.domain}", 
                    headers={'User-Agent': self.get_random_user_agent()},
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    # Extract domains using regex
                    pattern = r'<TD>([a-zA-Z0-9._-]+\.' + re.escape(self.domain) + ')</TD>'
                    subdomains = re.findall(pattern, response.text)
                    for subdomain in subdomains:
                        if subdomain not in self.subdomains and subdomain != self.domain:
                            self.subdomains.add(subdomain)
                            print(f"[+] Discovered from crt.sh (alt): {subdomain}")
            except Exception as e:
                print(f"[-] Error with alternative crt.sh search: {e}")
    
    def search_virustotal(self):
        print("\n[*] Searching VirusTotal for subdomains...")
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(
                f"https://www.virustotal.com/ui/domains/{self.domain}/subdomains?limit=40", 
                headers=headers, 
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', []):
                    subdomain = item.get('id')
                    if subdomain and subdomain not in self.subdomains:
                        self.subdomains.add(subdomain)
                        print(f"[+] Discovered from VirusTotal: {subdomain}")
        except Exception as e:
            print(f"[-] Error searching VirusTotal: {e}")
    
    def search_alienvault(self):
        print("\n[*] Searching AlienVault OTX for subdomains...")
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(
                f"https://otx.alienvault.com/api/v1/indicators/domain/{self.domain}/passive_dns", 
                headers=headers, 
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                for entry in data.get('passive_dns', []):
                    hostname = entry.get('hostname', '')
                    if hostname and self.domain in hostname and hostname not in self.subdomains:
                        self.subdomains.add(hostname)
                        print(f"[+] Discovered from AlienVault: {hostname}")
        except Exception as e:
            print(f"[-] Error searching AlienVault: {e}")
    
    def search_hackertarget(self):
        print("\n[*] Searching HackerTarget for subdomains...")
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(
                f"https://api.hackertarget.com/hostsearch/?q={self.domain}", 
                headers=headers, 
                timeout=self.timeout
            )
            if response.status_code == 200 and not response.text.startswith('error'):
                results = response.text.strip().split('\n')
                for result in results:
                    if ',' in result:
                        subdomain = result.split(',')[0]
                        if subdomain and subdomain not in self.subdomains:
                            self.subdomains.add(subdomain)
                            print(f"[+] Discovered from HackerTarget: {subdomain}")
        except Exception as e:
            print(f"[-] Error searching HackerTarget: {e}")
    
    def save_results(self):
        if not self.subdomains:
            print("\n[-] No subdomains found.")
            return
            
        try:
            with open(self.output_file, 'w') as f:
                for subdomain in sorted(self.subdomains):
                    f.write(f"{subdomain}\n")
            print(f"\n[+] Results saved to {self.output_file}")
            print(f"[+] Total unique subdomains found: {len(self.subdomains)}")
        except Exception as e:
            print(f"[-] Error saving results: {e}")
    
    def run(self):
        print(f"\n[*] Starting subdomain discovery for {self.domain}")
        print(f"[*] Results will be saved to {self.output_file}")
        
        # Create a thread pool for online sources
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            search_functions = [
                self.crt_sh_search,
                self.search_virustotal,
                self.search_alienvault,
                self.search_hackertarget
            ]
            executor.map(lambda fn: fn(), search_functions)
            
        # Then do brute force with wordlist
        wordlist = self.load_wordlist()
        if wordlist:
            print(f"\n[*] Starting DNS brute force with {len(wordlist)} subdomains...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
                executor.map(self.dns_brute_force, wordlist)
        
        # Save results to file
        self.save_results()

def main():
    parser = argparse.ArgumentParser(description='Subdomain finder tool')
    parser.add_argument('domain', help='Target domain to scan for subdomains')
    parser.add_argument('-w', '--wordlist', help='Path to wordlist file for brute forcing')
    parser.add_argument('-o', '--output', help='Output file to save results')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Number of threads for brute forcing')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout for HTTP requests in seconds')
    args = parser.parse_args()
    
    finder = SubdomainFinder(
        domain=args.domain,
        wordlist=args.wordlist,
        output=args.output,
        threads=args.threads,
        timeout=args.timeout
    )
    finder.run()

if __name__ == "__main__":
    main()