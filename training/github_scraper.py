"""
GitHub Scraper for CadQuery Examples
Searches GitHub for CadQuery code and downloads examples for training data.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict
import time


class GitHubScraper:
    """Scrapes GitHub for CadQuery examples using GitHub CLI."""
    
    def __init__(self, output_dir: str = "/home/dobbeltop/nexaai/training/data/github_examples"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.examples = []
        
    def search_repositories(self, max_repos: int = 100) -> List[Dict]:
        """Search GitHub for repositories containing CadQuery code."""
        print(f"🔍 Searching GitHub for CadQuery repositories...")
        
        # Search for repos with CadQuery code
        cmd = [
            "gh", "search", "repos",
            "cadquery language:python",
            "--limit", str(max_repos),
            "--json", "name,owner,description,url,stargazersCount"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            repos = json.loads(result.stdout)
            print(f"✓ Found {len(repos)} repositories")
            return repos
        except subprocess.CalledProcessError as e:
            print(f"✗ Error searching repositories: {e}")
            return []
    
    def search_code_files(self, max_files: int = 1000) -> List[Dict]:
        """Search GitHub for Python files containing CadQuery code."""
        print(f"🔍 Searching GitHub for CadQuery code files...")
        
        # Search for code files with CadQuery imports
        cmd = [
            "gh", "search", "code",
            "import cadquery language:python",
            "--limit", str(max_files),
            "--json", "path,repository,url"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            files = json.loads(result.stdout)
            print(f"✓ Found {len(files)} code files")
            return files
        except subprocess.CalledProcessError as e:
            print(f"✗ Error searching code: {e}")
            return []
    
    def download_file_content(self, repo_full_name: str, file_path: str) -> str:
        """Download the content of a specific file from a repository."""
        try:
            # Use gh api to get file content
            cmd = [
                "gh", "api",
                f"/repos/{repo_full_name}/contents/{file_path}",
                "--jq", ".content"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Content is base64 encoded, decode it
            import base64
            content = base64.b64decode(result.stdout.strip()).decode('utf-8')
            return content
        except Exception as e:
            print(f"✗ Error downloading {file_path}: {e}")
            return None
    
    def extract_cadquery_functions(self, code: str) -> List[str]:
        """Extract individual CadQuery code blocks from a file."""
        # Simple extraction: look for functions or standalone code blocks
        # that use CadQuery
        blocks = []
        
        # Split by function definitions
        lines = code.split('\n')
        current_block = []
        in_cadquery_block = False
        
        for line in lines:
            # Check if this line starts a new function or has CadQuery code
            if 'def ' in line or 'import cadquery' in line or 'cq.Workplane' in line:
                in_cadquery_block = True
            
            if in_cadquery_block:
                current_block.append(line)
                
                # End of block detection (simple heuristic)
                if line.strip() and not line.startswith(' ') and len(current_block) > 5:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                    in_cadquery_block = False
        
        # Add last block if exists
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return [b for b in blocks if 'cadquery' in b.lower()]
    
    def collect_examples(self, max_examples: int = 2000):
        """Main collection function."""
        print(f"\n{'='*60}")
        print(f"🚀 Starting GitHub CadQuery Example Collection")
        print(f"{'='*60}\n")
        
        # Search for code files
        files = self.search_code_files(max_files=max_examples)
        
        collected = 0
        for i, file_info in enumerate(files):
            if collected >= max_examples:
                break
            
            repo = file_info.get('repository', {})
            owner_login = repo.get('owner', {}).get('login', '') if isinstance(repo.get('owner'), dict) else ''
            repo_name = repo.get('name', '')
            repo_full_name = f"{owner_login}/{repo_name}"
            
            # Skip if we couldn't parse the repo name
            if not owner_login or not repo_name:
                print(f"  ✗ Skipping: Could not parse repository info")
                continue
            file_path = file_info.get('path', '')
            
            print(f"\n[{i+1}/{len(files)}] Downloading: {repo_full_name}/{file_path}")
            
            # Download file content
            content = self.download_file_content(repo_full_name, file_path)
            if not content:
                continue
            
            # Extract CadQuery code blocks
            blocks = self.extract_cadquery_functions(content)
            
            for j, block in enumerate(blocks):
                example = {
                    'id': f"github_{collected}",
                    'source': 'github',
                    'repo': repo_full_name,
                    'file': file_path,
                    'code': block,
                    'url': file_info.get('url', '')
                }
                
                self.examples.append(example)
                collected += 1
                
                # Save example to file
                example_file = self.output_dir / f"example_{collected}.json"
                with open(example_file, 'w') as f:
                    json.dump(example, f, indent=2)
            
            print(f"  ✓ Extracted {len(blocks)} code blocks (total: {collected})")
            
            # Rate limiting
            time.sleep(0.5)
        
        # Save summary
        summary = {
            'total_examples': len(self.examples),
            'source': 'github',
            'examples': self.examples
        }
        
        summary_file = self.output_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ Collection Complete!")
        print(f"  Total examples collected: {len(self.examples)}")
        print(f"  Saved to: {self.output_dir}")
        print(f"{'='*60}\n")
        
        return self.examples


if __name__ == "__main__":
    scraper = GitHubScraper()
    examples = scraper.collect_examples(max_examples=2000)
    print(f"\n✓ Collected {len(examples)} examples from GitHub")
