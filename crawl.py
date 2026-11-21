import requests
import pandas as pd
import re
import time

from bs4 import BeautifulSoup
from urllib.parse import urljoin

START_URL = "https://catalog.uconn.edu/graduate/courses/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)


def get_soup(url):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def get_subject_pages():

    soup = get_soup(START_URL)
    subjects = {}

    for link in soup.find_all("a", href=True):

        text = link.get_text(" ", strip=True)
        href = urljoin(START_URL, link["href"])

        match = re.search(r"\(([A-Z]{2,4})\)\s*$", text)

        if match and "/graduate/courses/" in href:
            subjects[match.group(1)] = href

    return subjects


def extract_courses(subject, url):

    soup = get_soup(url)
    courses = []

    blocks = soup.select(
        ".courseblock, .course-block"
    )

    for block in blocks:

        title_element = block.select_one(
            ".courseblocktitle, .course-title"
        )

        if not title_element:
            continue

        text = title_element.get_text(" ", strip=True)

        match = re.search(
            r"([A-Z]{2,4})\s+"
            r"(\d{4}[A-Z]?(?:-\d{4}[A-Z]?)?)"
            r"\s*[.:–-]\s*(.+)",
            text
        )

        if match:

            courses.append({
                "Subject Code": match.group(1),
                "Course Number": match.group(2),
                "Course Title": match.group(3).strip()
            })

    return courses


def main():

    print("Finding course subjects...")

    subjects = get_subject_pages()

    print(f"Found {len(subjects)} subjects.")

    all_courses = []

    for subject, url in subjects.items():

        print(f"Processing {subject}...")

        try:
            courses = extract_courses(subject, url)
            all_courses.extend(courses)

            print(f"Found {len(courses)} courses.")

        except Exception as e:
            print(f"Error with {subject}: {e}")

        time.sleep(0.5)

    # Create spreadsheet data
    df = pd.DataFrame(all_courses)

    if df.empty:
        print("No courses found. Check the website structure.")
        return

    # Remove duplicates
    df = df.drop_duplicates()

    # Sort by subject and course number
    df = df.sort_values(
        by=["Subject Code", "Course Number"]
    )

    # Save CSV
    df.to_csv(
        "UConn_Graduate_Courses.csv",
        index=False
    )

    print("\nFinished!")
    print(f"Total courses: {len(df)}")
    print("Saved as UConn_Graduate_Courses.csv")


if __name__ == "__main__":
    main()
