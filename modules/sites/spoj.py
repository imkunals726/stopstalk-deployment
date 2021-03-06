"""
    Copyright (c) 2015-2017 Raj Patel(raj454raj@gmail.com), StopStalk

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
"""

from .init import *

class Profile(object):
    """
        Class containing methods for retrieving
        submissions of user
    """

    # -------------------------------------------------------------------------
    def __init__(self, handle=""):
        """
            @param handle (String): Spoj handle
        """

        self.site = "Spoj"
        self.handle = handle

    # -------------------------------------------------------------------------
    @staticmethod
    def get_tags(problem_link):
        """
            Get the tags of a particular problem from its URL

            @param problem_link (String): Problem URL
            @return (List): List of tags for that problem
        """

        # Temporary hack - spoj seems to have removed their SSL cert
        problem_link = problem_link.replace("https", "http")
        response = get_request(problem_link)
        if response in REQUEST_FAILURES:
            return ["-"]

        tags = BeautifulSoup(response.text, "lxml").find_all("div",
                                                             id="problem-tags")
        try:
            tags = tags[0].findAll("span")
        except IndexError:
            return ["-"]
        all_tags = []

        for tag in tags:
            tmp = tag.contents
            if tmp != []:
                all_tags.append(tmp[0][1:])

        return all_tags

    # -------------------------------------------------------------------------
    def get_submissions(self, last_retrieved):
        """
            Retrieve Spoj submissions after last retrieved timestamp

            @param last_retrieved (DateTime): Last retrieved timestamp for the user
            @return (Dict): Dictionary of submissions containing all the
                            information about the submissions
        """

        handle = self.handle
        submissions = {handle: {}}
        start = 0
        it = 1

        previd = -1
        currid = 0
        page = 0
        url = current.SITES[self.site] + "users/" + handle
        tmpreq = get_request(url)

        if tmpreq in REQUEST_FAILURES:
            return tmpreq

        # Bad but correct way of checking if the handle exists
        if tmpreq.text.find("History of submissions") == -1:
            return NOT_FOUND

        while 1:
            flag = 0
            url = current.SITES[self.site] + "status/" + \
                  handle + \
                  "/all/start=" + \
                  str(start)

            start += 20
            t = get_request(url)
            if t in REQUEST_FAILURES:
                return t

            soup = bs4.BeautifulSoup(t.text, "lxml")
            table_body = soup.find("tbody")

            # Check if the page retrieved has no submissions
            if len(table_body) == 1:
                return submissions

            row = 0
            submissions[handle][page] = {}
            for i in table_body:
                submissions[handle][page][it] = []
                submission = submissions[handle][page][it]
                append = submission.append

                if isinstance(i, bs4.element.Tag):
                    if row == 0:
                        currid = i.contents[1].contents[0]
                        if currid == previd:
                            flag = 1
                            break
                    row += 1
                    previd = currid

                    # Time of submission
                    tos = i.contents[3].contents[1].contents[0]
                    curr = time.strptime(str(tos), "%Y-%m-%d %H:%M:%S")
                    if curr <= last_retrieved:
                        return submissions
                    append(str(tos))

                    # Problem Name/URL
                    uri = i.contents[5].contents[0]
                    uri["href"] = "https://www.spoj.com" + uri["href"]
                    problem_link = eval(repr(uri["href"]).replace("\\", ""))
                    append(problem_link)
                    append(uri.contents[0].strip())

                    # Problem Status
                    status = str(i.contents[6])
                    if status.__contains__("accepted"):
                        submission_status = "AC"
                    elif status.__contains__("wrong"):
                        submission_status = "WA"
                    elif status.__contains__("compilation"):
                        submission_status = "CE"
                    elif status.__contains__("runtime"):
                        submission_status = "RE"
                    elif status.__contains__("time limit"):
                        submission_status = "TLE"
                    else:
                        submission_status = "OTH"

                    append(submission_status)

                    # Question Points
                    if submission_status == "AC":
                        points = "100"
                    else:
                        points = "0"
                    append(points)

                    # Language
                    append(i.contents[12].contents[1].contents[0])

                    # View code Link
                    view_link = ""
                    append(view_link)

                    it += 1

            page += 1

            if flag == 1:
                break

        return submissions

# =============================================================================
