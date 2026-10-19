from app.services.pubmed import discover_publications


def main():
    researcher = "Aileen J. Anderson"
    orcid = "0000-0002-8203-8891"

    print(f"Searching publications for {researcher}...")
    print(f"ORCID: {orcid}\n")

    publications = discover_publications(orcid)

    print(f"Found {len(publications)} publications\n")

    for publication in publications:
        print("-" * 60)
        print(f"PMID: {publication['pmid']}")
        print(f"Title: {publication['title']}")
        print(f"Journal: {publication['journal']}")
        print(f"Date: {publication['publication_date']}")
        print(f"Authors: {', '.join(publication['authors'])}")

    print("\nDiscovery completed!")


if __name__ == "__main__":
    main()