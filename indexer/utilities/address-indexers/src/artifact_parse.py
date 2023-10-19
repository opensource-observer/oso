import re
from urllib.parse import urlparse


class Parser:
    @classmethod
    def parse_url(cls, url, domain_check, success_callback):
        if not isinstance(url, str):
            return "error: no data", None
        
        url = url.strip().lower()
        
        if not domain_check(url):
            return "error: no data", None

        paths = urlparse(url).path.split('/')
        if not len(paths) > 1 or paths[1] == "":
            return "error: no data", None
        
        return success_callback(url)

    @classmethod
    def extract_matches(cls, url, pattern):
        matches = re.findall(pattern, url)
        return "success", matches[0] if matches else None

    @classmethod
    def github(cls, url):
        def github_domain_check(url):
            return 'github.com' in url
        
        def github_success_callback(url):
            paths = urlparse(url).path.split('/')
            if len(paths) == 2 and "?" not in paths[1]:
                return "success", paths[1]
            elif len(paths) == 3 and "?" not in paths[2]:
                return "success", paths[1] + "/" + paths[2]
            return f"review: {url}", None
        
        return cls.parse_url(url, github_domain_check, github_success_callback)

    @classmethod
    def etherscan(cls, url):
        def etherscan_domain_check(url):
            return 'etherscan.io' in url
        
        def etherscan_success_callback(url):
            eth_address_pattern = r'(0x[a-fA-F0-9]{40})'
            return cls.extract_matches(url, eth_address_pattern)
        
        return cls.parse_url(url, etherscan_domain_check, etherscan_success_callback)

    @classmethod
    def npm(cls, url):
        def npm_domain_check(url):
            return 'npmjs.com' in url or 'npm.im' in url or 'npm-stat' in url
        
        def npm_success_callback(url):
            if 'npmjs.com' in url: 
                paths = urlparse(url).path.split('/')
                return "success", "/".join(paths[2:])
            if 'npm.im' in url:
                paths = urlparse(url).path.split('/')
                return "success", "/".join(paths[1:])
            if 'npm-stat' in url:
                package = url.split('?package=')[1].split('&')[0]
                package = package.replace('%40', '@').replace('%2f', '/')
                return "success", package
            return f"review: {url}", None
        
        return cls.parse_url(url, npm_domain_check, npm_success_callback)

# Usage example:
result, data = Parser.github("https://github.com/myorg/repo")
print(result, data)
