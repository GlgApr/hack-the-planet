# @title DNS Zone Transfer Checker
# @markdown Use: python dns_zone_transfer.py <domain> <nameserver>
# @Galang Aprilian - 2025
import dns.query
import dns.zone
import dns.resolver
import sys
import argparse

def get_nameservers(domain):
    """Mendapatkan nama server untuk domain"""
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        return [str(answer.target).rstrip('.') for answer in answers]
    except Exception as e:
        print(f"Error mendapatkan nameservers untuk {domain}: {e}")
        return []

def try_zone_transfer(domain, nameserver):
    """Mencoba zone transfer dari nameserver"""
    print(f"\nMencoba Zone Transfer dari {nameserver} untuk {domain}")
    try:
        # Coba melakukan zone transfer
        zone = dns.zone.from_xfr(dns.query.xfr(nameserver, domain, timeout=10))
        
        # Jika berhasil, tampilkan semua record
        print(f"[+] Zone Transfer berhasil untuk {domain} dari {nameserver}!")
        
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
                    print(f"  {name} {rdataset.ttl} {record['class']} {record['type']} {record['data']}")
        
        # Simpan hasil ke file
        output_file = f"zone_transfer_{domain}_from_{nameserver}.txt"
        with open(output_file, 'w') as f:
            f.write(f"Zone Transfer berhasil untuk {domain} dari {nameserver}\n")
            f.write("=" * 60 + "\n\n")
            for record in records:
                f.write(f"{record['name']} {record['ttl']} {record['class']} {record['type']} {record['data']}\n")
        
        print(f"[+] Hasil disimpan ke {output_file}")
        return True
    except Exception as e:
        print(f"[-] Zone Transfer gagal: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='DNS Zone Transfer Checker')
    parser.add_argument('domain', help='Domain yang akan dicek (contoh: itn.ac.id)')
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

if __name__ == "__main__":
    main()