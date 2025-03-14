# @title Subdomain Network Visualizer
# @markdown Upload your subdomain .txt file and create a beautiful network visualization
# @Galang Aprilian - 2025

import matplotlib.pyplot as plt
import networkx as nx
import os
from urllib.parse import urlparse
import random
import colorsys
from google.colab import files
import io
import base64
from IPython.display import HTML, display, Image

# File Upload Section
uploaded = files.upload()
file_name = list(uploaded.keys())[0]

class SubdomainVisualizer:
    def __init__(self, input_file, output_file=None, theme='dark', layout='spring'):
        self.input_file = input_file
        self.output_file = output_file or f"subdomain_visualization_{os.path.basename(input_file).split('.')[0]}.png"
        self.theme = theme
        self.layout_type = layout
        self.subdomains = []
        self.G = nx.Graph()
        
        # Theme settings
        self.themes = {
            'dark': {
                'bg_color': '#121212',
                'edge_color': '#2A2A2A',
                'node_colors': self.generate_color_palette(base_hue=0.6),  # Blue-based
                'font_color': '#FFFFFF',
                'alpha': 0.85
            },
            'light': {
                'bg_color': '#F8F9FA',
                'edge_color': '#DDDDDD',
                'node_colors': self.generate_color_palette(base_hue=0.1),  # Orange-based
                'font_color': '#333333',
                'alpha': 0.75
            },
            'cyberpunk': {
                'bg_color': '#0C0C14',
                'edge_color': '#00FFFF',
                'node_colors': self.generate_color_palette(base_hue=0.9, saturation=0.8),  # Neon colors
                'font_color': '#FFFFFF',
                'alpha': 0.9
            },
            'matrix': {
                'bg_color': '#000000',
                'edge_color': '#00FF00',
                'node_colors': self.generate_color_gradient(start_color=(0, 0.8, 0), end_color=(0.3, 1, 0.3)),
                'font_color': '#00FF00',
                'alpha': 0.85
            },
            'sunset': {
                'bg_color': '#170F2B',
                'edge_color': '#D6655A',
                'node_colors': self.generate_color_gradient(start_color=(0.05, 0.8, 0.9), end_color=(0.17, 0.8, 0.9)),
                'font_color': '#FFFFFF',
                'alpha': 0.9
            }
        }
        
    def generate_color_palette(self, base_hue=0.6, saturation=0.6, value=0.9, count=10):
        """Generate color palette with variations around a base hue"""
        colors = []
        for i in range(count):
            hue = (base_hue + i * 0.1) % 1.0
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            # Convert to hex
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )
            colors.append(hex_color)
        return colors
    
    def generate_color_gradient(self, start_color=(0.6, 0.6, 0.9), end_color=(0.1, 0.6, 0.9), count=10):
        """Generate a gradient between two colors"""
        start_h, start_s, start_v = start_color
        end_h, end_s, end_v = end_color
        
        colors = []
        for i in range(count):
            t = i / (count - 1)
            h = start_h + t * (end_h - start_h)
            s = start_s + t * (end_s - start_s)
            v = start_v + t * (end_v - start_v)
            
            rgb = colorsys.hsv_to_rgb(h, s, v)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )
            colors.append(hex_color)
        return colors
        
    def load_subdomains_from_content(self, content):
        try:
            lines = content.decode('utf-8').splitlines()
                
            self.subdomains = []
            for line in lines:
                subdomain = line.strip()
                if subdomain:
                    # Clean the subdomain if it has http:// or https://
                    if '://' in subdomain:
                        subdomain = urlparse(subdomain).netloc
                    self.subdomains.append(subdomain)
                    
            print(f"[+] Loaded {len(self.subdomains)} subdomains")
            return True
        except Exception as e:
            print(f"[-] Error loading subdomains: {e}")
            return False
            
    def analyze_structure(self):
        if not self.subdomains:
            print("[-] No subdomains loaded")
            return False
            
        # Extract base domain from first subdomain
        parts = self.subdomains[0].split('.')
        base_domain = '.'.join(parts[-2:])  # e.g., example.com
        
        # Add base domain as central node
        self.G.add_node(base_domain, size=1500, level=0, type='base')
        
        levels = {}
        max_level = 0
        
        # Process each subdomain
        for subdomain in self.subdomains:
            if subdomain == base_domain:
                continue
                
            # Get subdomain parts
            parts = subdomain.split('.')
            
            # Skip if this doesn't match our base domain
            if len(parts) < 2 or '.'.join(parts[-2:]) != base_domain:
                continue
                
            # Calculate level (depth of subdomain)
            level = len(parts) - 2
            max_level = max(max_level, level)
            
            # Store subdomains by level
            if level not in levels:
                levels[level] = []
            levels[level].append(subdomain)
            
            # Add node for this subdomain
            node_size = 900 / (level + 1)  # Size decreases with level
            self.G.add_node(subdomain, size=node_size, level=level, type='subdomain')
            
            # Create edges based on domain hierarchy
            if level == 1:
                # Direct connection to base domain
                self.G.add_edge(base_domain, subdomain, weight=3)
            else:
                # Connect to parent domain
                parent = '.'.join(parts[1:])
                if parent in self.G:
                    self.G.add_edge(parent, subdomain, weight=2)
                else:
                    # If parent not in graph, connect to base
                    self.G.add_edge(base_domain, subdomain, weight=1)
        
        print(f"[+] Created graph with {self.G.number_of_nodes()} nodes and {self.G.number_of_edges()} edges")
        print(f"[+] Maximum subdomain depth: {max_level}")
        return True
            
    def create_visualization(self):
        if not self.G.nodes():
            print("[-] Graph is empty, nothing to visualize")
            return False
            
        # Get theme settings
        theme = self.themes.get(self.theme, self.themes['dark'])
        
        # Setup figure with proper DPI for high quality
        plt.figure(figsize=(16, 12), facecolor=theme['bg_color'], dpi=300)
        
        # Select layout algorithm
        if self.layout_type == 'spring':
            pos = nx.spring_layout(self.G, k=0.3, iterations=50, seed=42)
        elif self.layout_type == 'radial':
            pos = nx.kamada_kawai_layout(self.G)
        elif self.layout_type == 'spiral':
            pos = nx.spiral_layout(self.G)
        elif self.layout_type == 'circular':
            pos = nx.circular_layout(self.G)
        else:
            pos = nx.spring_layout(self.G, k=0.3, iterations=50, seed=42)
        
        # Prepare node styling
        node_sizes = [self.G.nodes[node]['size'] for node in self.G.nodes()]
        
        # Color nodes by level
        node_colors = []
        for node in self.G.nodes():
            level = self.G.nodes[node]['level']
            color_idx = min(level, len(theme['node_colors'])-1)
            node_colors.append(theme['node_colors'][color_idx])
        
        # Draw edges with alpha for better visualization
        nx.draw_networkx_edges(
            self.G, pos, 
            alpha=theme['alpha'],
            edge_color=theme['edge_color'],
            width=0.8
        )
        
        # Draw nodes with custom colors and sizes
        nx.draw_networkx_nodes(
            self.G, pos,
            node_size=node_sizes,
            node_color=node_colors,
            alpha=0.9,
            edgecolors=theme['edge_color'],
            linewidths=0.5
        )
        
        # Draw labels for important nodes only (base domain and first level)
        important_nodes = {node: node for node in self.G.nodes()}
        
        nx.draw_networkx_labels(
            self.G, pos,
            labels=important_nodes,
            font_size=7,
            font_color=theme['font_color'],
            font_weight='bold'
        )
        
        # Add a legend for different levels
        legend_elements = []
        
        # Add title with total count
        subdomain_count = len(self.G.nodes()) - 1  # Subtract 1 for base domain
        plt.suptitle(f"Subdomain Network: {subdomain_count} subdomains", 
                  fontsize=16, color=theme['font_color'], y=0.98)
        
        # Add source file info
        plt.figtext(0.99, 0.01, f"Source: {os.path.basename(self.input_file)}", 
                 horizontalalignment='right', color=theme['font_color'], fontsize=8)
        
        plt.axis('off')
        plt.tight_layout()
        
        # Save the figure to a BytesIO object
        img_data = io.BytesIO()
        plt.savefig(img_data, format='png', facecolor=theme['bg_color'], bbox_inches='tight', dpi=300)
        img_data.seek(0)
        
        # Also save to file
        plt.savefig(self.output_file, facecolor=theme['bg_color'], bbox_inches='tight', dpi=300)
        print(f"[+] Visualization saved to {self.output_file}")
        
        return img_data

# Add interactive widgets for theme and layout selection
import ipywidgets as widgets
from IPython.display import display

# @title Visualization Options
theme = widgets.Dropdown(
    options=['dark', 'cyberpunk', 'matrix', 'sunset', 'light'],
    value='dark',
    description='Theme:',
)
display(theme)

layout = widgets.Dropdown(
    options=['spring', 'radial', 'spiral', 'circular'],
    value='spring',
    description='Layout:',
)
display(layout)

# Function to run visualization
def run_visualization(b):
    # Clear output for cleaner display
    from IPython.display import clear_output
    clear_output(wait=True)
    
    print(f"Processing file: {file_name}")
    print(f"Selected theme: {theme.value}")
    print(f"Selected layout: {layout.value}")
    
    # Create visualizer
    visualizer = SubdomainVisualizer(
        input_file=file_name,
        theme=theme.value,
        layout=layout.value
    )
    
    # Load and process subdomains
    if visualizer.load_subdomains_from_content(uploaded[file_name]):
        visualizer.analyze_structure()
        img_data = visualizer.create_visualization()
        
        # Display the image
        display(Image(data=img_data.getvalue()))
        
        # Provide download button
        files.download(visualizer.output_file)

# Create and display the run button
run_button = widgets.Button(
    description='Generate Visualization',
    button_style='success',
    tooltip='Click to generate the visualization'
)
run_button.on_click(run_visualization)
display(run_button)

# Display filename
print(f"Uploaded file: {file_name}")
print("Select options above and click 'Generate Visualization' to create subdomain network map")