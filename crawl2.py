import requests
import csv
import re
import time

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# settings
START_URL = "https://catalog.uconn.edu/graduate/courses/"

OUTPUT_FILE = "UConn_Graduate_Courses.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)


# download, parse web pages
def get_soup(url):
    response = session.get(url, timeout=30)
    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


# find subject links
def get_subject_links():
    print("Opening graduate course directory...")

    soup = get_soup(START_URL)
    subjects = []

    for link in soup.find_all("a", href=True):
        subject_name = link.get_text(" ", strip=True)

        subject_url = urljoin(
            START_URL,
            link["href"]
        )

        # extract subject code 
        match = re.search(
            r"\(([A-Z]{2,4})\)\s*$",
            subject_name
        )

        if not match:
            continue

        subject_code = match.group(1)

        # only accept individual graduate course pages.
        path = urlparse(subject_url).path

        if not re.fullmatch(
            r"/graduate/courses/[^/]+/?",
            path
        ):
            continue

        subjects.append({
            "subject": subject_code,
            "name": subject_name,
            "url": subject_url
        })

    # remove duplicate subject links
    unique_subjects = {}

    for subject in subjects:
        unique_subjects[subject["url"]] = subject

    subjects = list(unique_subjects.values())

    print(f"Found {len(subjects)} subject pages.\n")

    return subjects


# visit each subject page

def get_courses(subject):
    subject_code = subject["subject"]
    subject_name = subject["name"]
    subject_url = subject["url"]

    print(f"Opening {subject_name}...")

    soup = get_soup(subject_url)
    courses = []
    course_titles = soup.select(
        ".courseblocktitle"
    )

    # alternative selector for diff page layouts
    if not course_titles:
        course_titles = soup.select(
            ".course-title"
        )

    for element in course_titles:
        text = element.get_text(" ", strip=True)
        match = re.search(
            r"^([A-Z]{2,4})\s+"
            r"(\d{4}[A-Z]?(?:\s*-\s*\d{4}[A-Z]?)?)"
            r"\.\s*(.+?)"
            r"(?:\s*\(\d+\s+Credits?\))?$",
            text
        )

        if not match:
            continue

        code = match.group(1)
        number = match.group(2)
        title = match.group(3).strip()

        if code != subject_code:
            continue

        courses.append({
            "Subject Code": code,
            "Course Number": number,
            "Course Title": title
        })

    print(f"  Found {len(courses)} courses.\n")

    return courses


# scrape all subjects

def scrape_catalog():

    subjects = get_subject_links()

    all_courses = []

    for subject in subjects:

        try:

            courses = get_courses(subject)

            all_courses.extend(courses)

        except requests.RequestException as error:

            print(
                f"Error accessing {subject['name']}: {error}"
            )

        except Exception as error:

            print(
                f"Unexpected error: {error}"
            )

        # Pause between requests.
        time.sleep(0.5)

    return all_courses



# save data to csv
def save_courses(courses):
    unique_courses = {}

    for course in courses:
        key = (
            course["Subject Code"],
            course["Course Number"],
            course["Course Title"]
        )
        unique_courses[key] = course
    courses = list(unique_courses.values())

    courses.sort(
        key=lambda x: (
            x["Subject Code"],
            x["Course Number"]
        )
    )

    # write csv file
    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)
        writer.writerow([
            "Subject Code",
            "Course Number",
            "Course Title"
        ])

        for course in courses:

            writer.writerow([
                course["Subject Code"],
                course["Course Number"],
                course["Course Title"]
            ])

    print("----------------------------------")
    print("scraping complete")
    print("----------------------------------")

    print(f"Total courses: {len(courses)}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    print("Starting Course Scraper\n")
    courses = scrape_catalog()

    if courses:
        save_courses(courses)
    else:

        print("No courses were found.")
        print("Check the website HTML and selectors.")
