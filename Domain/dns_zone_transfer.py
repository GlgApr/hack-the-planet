#!/usr/bin/env python3
# @title DNS Zone Transfer Checker - Fixed
# @markdown Use: python dns_zone_transfer_fixed.py <domain> [--nameserver <ns>]
# @Galang Aprilian - 2025 (Fixed by Claude haha)
import dns.resolver
import dns.zone
import dns.query
import sys
import argparse
import os
import time
import socket
from datetime import datetime

def get_nameservers(domain):
    """Mendapatkan nama server untuk domain"""
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        return [str(answer.target).rstrip('.') for answer in answers]
    except Exception as e:
        print(f"Error mendapatkan nameservers untuk {domain}: {e}")
        return []

def get_nameserver_ip(nameserver):
    """Mendapatkan IP address dari nameserver"""
    try:
        return socket.gethostbyname(nameserver)
    except socket.gaierror:
        print(f"Error: Tidak dapat mendapatkan IP address untuk {nameserver}")
        return None

def try_zone_transfer(domain, nameserver):
    """Mencoba zone transfer dari nameserver menggunakan modul dnspython"""
    print(f"\nMencoba Zone Transfer dari {nameserver} untuk {domain}")
    
    # Dapatkan IP dari nameserver
    nameserver_ip = get_nameserver_ip(nameserver)
    if not nameserver_ip:
        print(f"[-] Zone Transfer gagal: Tidak dapat mendapatkan IP address untuk {nameserver}")
        return False
    
    try:
        # Coba dengan explicit IPv4 address
        print(f"  Menggunakan IP address nameserver: {nameserver_ip}")
        zone = dns.zone.from_xfr(dns.query.xfr(nameserver_ip, domain, timeout=30, lifetime=30))
        
        # Jika kode mencapai sini, berarti zone transfer berhasil
        print(f"[+] Zone Transfer berhasil untuk {domain} dari {nameserver}!")
        
        # Proses dan simpan hasil zone transfer
        output_file = f"zone_transfer_{domain}_from_{nameserver}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        records = []
        for name, node in zone.nodes.items():
            rdatasets = node.rdatasets
            for rdataset in rdatasets:
                for rdata in rdataset:
                    record = {
                        'name': name,
                        'ttl': rdataset.ttl,
                        'class': dns.rdataclass.to_text(rdataset.rdclass),
                        'type': dns.rdatatype.to_text(rdataset.rdtype),
                        'data': rdata.to_text()
                    }
                    records.append(record)
        
        # Tampilkan hasil di layar (maksimal 10 record)
        print("\nRecord yang ditemukan:")
        for i, record in enumerate(records):
            if i < 10:
                name_text = "@" if str(record['name']) == "." else str(record['name'])
                print(f"  {name_text} {record['ttl']} {record['class']} {record['type']} {record['data']}")
            else:
                print(f"  ... dan {len(records) - 10} record lainnya")
                break
        
        # Simpan hasil lengkap ke file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Zone Transfer berhasil untuk {domain} dari {nameserver} ({nameserver_ip})\n")
            f.write(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            for record in records:
                name_text = "@" if str(record['name']) == "." else str(record['name'])
                f.write(f"{name_text} {record['ttl']} {record['class']} {record['type']} {record['data']}\n")
        
        print(f"\n[+] Hasil lengkap disimpan ke {output_file}")
        return True
        
    except dns.xfr.TransferError as e:
        print(f"[-] Zone Transfer gagal: Transfer Error - {e}")
        return False
    except dns.exception.Timeout:
        print(f"[-] Zone Transfer gagal: Timeout - Tidak ada respons dari server dalam waktu yang ditentukan")
        return False
    except dns.exception.FormError:
        print(f"[-] Zone Transfer gagal: Form Error - Server menolak permintaan zone transfer")
        return False
    except socket.gaierror as e:
        print(f"[-] Zone Transfer gagal: Socket Error - {e}")
        return False
    except ValueError as e:
        print(f"[-] Zone Transfer gagal: ValueError - {e if str(e) else 'Tidak ada data yang diterima dari server'}")
        
        # Coba lagi dengan port 53 yang eksplisit
        try:
            print(f"  Mencoba lagi dengan port 53 eksplisit...")
            zone = dns.zone.from_xfr(dns.query.xfr(nameserver_ip, domain, port=53, timeout=30, lifetime=30))
            print(f"[+] Zone Transfer berhasil pada percobaan kedua!")
            # Proses dan simpan hasilnya (kode yang sama dengan di atas)
            return True
        except Exception as e2:
            print(f"  Percobaan kedua juga gagal: {type(e2).__name__} - {e2}")
            return False
    except Exception as e:
        print(f"[-] Zone Transfer gagal: {type(e).__name__} - {e}")
        return False

def check_dependencies():
    """Memeriksa apakah semua modul yang diperlukan tersedia"""
    try:
        # Cek versi dnspython
        import dns
        print(f"Menggunakan dnspython versi {dns.__version__}")
        if dns.__version__.split('.')[0] < '2':
            print("Peringatan: Versi dnspython yang direkomendasikan adalah 2.0.0 atau lebih baru.")
        
        import dns.resolver
        import dns.zone
        import dns.query
        return True
    except ImportError:
        print("Error: Modul dnspython tidak ditemukan.")
        print("Silakan install dengan perintah: pip install dnspython")
        return False

def main():
    # Periksa dependencies
    if not check_dependencies():
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='DNS Zone Transfer Checker - Fixed')
    parser.add_argument('domain', help='Domain yang akan dicek (contoh: zonetransfer.me)')
    parser.add_argument('-n', '--nameserver', help='Nameserver spesifik untuk dicek')
    args = parser.parse_args()
    
    domain = args.domain
    
    print(f"Pengecekan DNS Zone Transfer untuk {domain}")
    print("=" * 60)
    
    if args.nameserver:
        nameservers = [args.nameserver]
    else:
        # Dapatkan semua nameservers untuk domain
        print(f"\nMendapatkan nameservers untuk {domain}...")
        nameservers = get_nameservers(domain)
        
        if not nameservers:
            print("Tidak dapat menemukan nameservers. Periksa domain dan koneksi internet Anda.")
            sys.exit(1)
        
        print(f"Nameservers untuk {domain}:")
        for ns in nameservers:
            print(f"  - {ns}")
    
    # Coba zone transfer untuk setiap nameserver
    success = False
    for nameserver in nameservers:
        if try_zone_transfer(domain, nameserver):
            success = True
    
    if not success:
        print("\n[-] Semua percobaan zone transfer gagal.")
        print("Ini berarti domain terkonfigurasi dengan baik dari segi keamanan DNS Zone Transfer.")
    else:
        print("\n[!] PERHATIAN: Zone Transfer diizinkan!")
        print("Ini merupakan potensi masalah keamanan yang harus diperbaiki.")
        
    # Pause pada Windows agar user dapat melihat hasil sebelum jendela konsol tertutup
    if os.name == 'nt':  # Windows
        print("\nTekan Enter untuk keluar...")
        input()

if __name__ == "__main__":
    main()
