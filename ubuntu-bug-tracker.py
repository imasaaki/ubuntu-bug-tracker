import datetime
import requests
import re

page_1804_true_dict = dict()
page_1804_false_dict = dict()

def add_dict(a_dict, a_url, a_title):
    if a_url in a_dict:
        print('duplicate url:' + a_url)
        return
    a_dict[a_url] = a_title
    print('add url:' + a_url)

def getBugList(a_url, task):
    print(a_url, task)
    url = a_url
    response = requests.get(url)
    response.encoding = response.apparent_encoding

    noreturn_text = response.text.replace('\n', '').replace('\r', '').replace(' ', '')
    pattern_url = r'ahref="(https:\/\/bugs.launchpad.net\/ubuntu\/(\+source\/\S{0,50}\/|)\+bug\/\d+)"class='
    pattern_importance = r'<divclass="importanceimportance.{1,30}">(.{1,30})<\/div>'
    pattern_status = r'<divclass="statusstatus.{1,30}">(.{1,30})<\/div>'
    pattern_totalnumber = r'of(\d{1,10})results'
    # matches_url = re.findall(pattern_url, noreturn_text)
    # matches_importance = re.findall(pattern_importance, noreturn_text)
    # matches_status = re.findall(pattern_status, noreturn_text)
    matches_totalnumber = re.findall(pattern_totalnumber, noreturn_text)

    total_number = int(matches_totalnumber[0])
    # int(total_number)

    # matches_importance
    # print(type(matches_importance))
    # print(type(matches_importance[0]))
    # print(matches_importance)
    # print(noreturn_text)

    # with open('matches_url.txt', mode='w') as out_file:
    #     # ２回ずつ取得されるので重複削除
    #     for match in list(set(matches_url)):    
    #         out_file.write(match + '\r\n')

    # with open('matches_importance.txt', mode='w') as out_file:
    #     for match in matches_importance:   
    #         out_file.write(match + '\r\n')

    # with open('matches_status.txt', mode='w') as out_file:
    #     for match in matches_status:    
    #         out_file.write(match + '\r\n')

    # json-cache-scriptから
    pattern_lastupdate = r'"last_updated":"on(\d\d\d\d-\d\d-\d\d)"'
    pattern_milestone = r'"milestone_name":(\S{1,50}),"tags":'
    # matches_lastupdate = re.findall(pattern_lastupdate, noreturn_text)
    # matches_milestone = re.findall(pattern_milestone, noreturn_text)

    # with open('matches_lastupate.txt', mode='w') as out_file:
    #     for match in matches_lastupdate:   
    #         out_file.write(match + '\r\n')

    # with open('matches_milestion.txt', mode='w') as out_file:
    #     for match in matches_milestone:    
    #         out_file.write(match + '\r\n')

    with open('result.html', 'w', encoding='utf-8') as f:
        f.write(response.text)

    # だんだんURLが長くなっているような、線形に増えるいるわけではないので予測できない
    pattern_nexturl = r'"next"href="(https:\S{0,5000})"id=\S{0,200}><strong>Next'
    matches_nexturl = re.findall(pattern_nexturl, noreturn_text)
    next_url = matches_nexturl[0]
    single_pange_number = 75
    # tmp_number = 160

    # +を追加しておく（エクセルでリストを作る都合上、＋を削除した経緯がある）
    excludes_set = set('+' + line.strip() for line in open('excludes.txt'))

    count = 0
    with open("output_" + task + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv', mode='a') as out_file:
        out_file.write('"url","module","title","importance","status","lastupdate"' + '\r\n')
        for i in range(0, int(total_number/single_pange_number) + 1):
            matches_url = re.findall(pattern_url, noreturn_text)
            matches_importance = re.findall(pattern_importance, noreturn_text)
            matches_status = re.findall(pattern_status, noreturn_text)
            matches_lastupdate = re.findall(pattern_lastupdate, noreturn_text)
            matches_milestone = re.findall(pattern_milestone, noreturn_text)

            # with open('result' + str(i) + '.html', 'w', encoding='utf-8') as f:
            #     f.write(response.text)
            
            try:
                for j in range(len(matches_url)):

                    title = ""

                    # ubuntu 1804のことがどうかチェックする
                    is_ubuntu1804 = False
                    dt_bug = datetime.datetime.strptime(matches_lastupdate[j], '%Y-%m-%d')
                    dt_1804_release = datetime.datetime(2018, 4, 1)

                    # ubuntu18.0.4リリースの一週間前
                    dt_180404_release = datetime.datetime(2020, 2, 1)

                    # ubuntu 1804 release前のものは見ない
                    # ubuntu 1804.4のrelease少し前にクローズしたものは見ない
                    if dt_bug > dt_1804_release and (matches_status[j] != "FixReleased" or dt_bug > dt_180404_release) and (not (matches_url[j][1] in excludes_set)):
                        # 一度見たものはもう見ない
                        if matches_url[j][0] in page_1804_true_dict:
                            is_ubuntu1804 = True
                            title = page_1804_true_dict[matches_url[j][0]]
                            print('hit true cache: ' + matches_url[j][0])
                        elif matches_url[j][0] in page_1804_false_dict:
                            is_ubuntu1804 = False
                            title = page_1804_false_dict[matches_url[j][0]]
                            print('hit false cache: ' + matches_url[j][0])
                        else:
                            print('no cache: ' + matches_url[j][0])
                            response_bugpage = requests.get(matches_url[j][0])
                            response_bugpage.encoding = response.apparent_encoding
                            pattern_title_in_sigle_page = r'<h1 id="edit-title">\n.*\n(.*)\n.*\n.*\n<\/h1>'
                            matches_title = re.findall(pattern_title_in_sigle_page, response_bugpage.text)
                            title = matches_title[0]
                            if '18.04' in response_bugpage.text:
                                is_ubuntu1804 = True
                                add_dict(page_1804_true_dict, matches_url[j][0], title)
                            else:
                                add_dict(page_1804_false_dict, matches_url[j][0], title)
                                            
                        ## +sourceとバックスラッシュが、後工程で邪魔なので削除
                        # if len(matches_url[j][1]) > 0:
                        #    matches_url[j][1] = matches_url[j][1].replace("+source","").replace("/", "")
                        if is_ubuntu1804 == True:
                            out_file.write('"{}","{}","{}","{}","{}","{}"\r\n'.format(
                                matches_url[j][0],
                                matches_url[j][1],
                                title.replace("\"", ""), # ダブルクォーテーションを削除
                                matches_importance[j],
                                matches_status[j],
                                matches_lastupdate[j]))

                    count = count + 1
                    print(str(count) + '/' + str(total_number))
            except:
                print("loop error")

            # 100回ぐらい順番に進むとログイン画面になる    
            # if (len(matches_url) < single_pange_number):
            #     break

            # matches_nexturl = re.findall(pattern_nexturl, noreturn_text)
            # url = matches_nexturl[0]
            url = next_url
            print(url)
            # print(len(url))

            response = requests.get(url)
            response.encoding = response.apparent_encoding
            noreturn_text = response.text.replace('\n', '').replace('\r', '').replace(' ', '')
            next_page = (i + 2) * single_pange_number
            next_url = re.sub(r'memo=\d+&amp;start=\d+', 'memo={}&amp;start={}'.format(next_page, next_page), next_url)
            print('count={}, i={}, next_page={}'.format(count, i, next_page))

try:
    v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
    getBugList(v_url, "CRITICAL")
except:
    print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "HIGH")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
#     getBugList(v_url, "HIGH_order1")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
#     getBugList(v_url, "HIGH_order2")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "Medium")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
#     getBugList(v_url, "Medium_order1")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
#     getBugList(v_url, "Medium_order2")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=18.04&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "Ubuntu1804")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=UNDECIDED&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "Undecided")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=UNDECIDED&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
#     getBugList(v_url, "Undecided_order1")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=UNDECIDED&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
#     getBugList(v_url, "Undecided_order2")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=UNKNOWN&field.importance%3Alist=UNDECIDED&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "FIXR_UNKOWNUNDECIDED")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=UNKNOWN&field.importance%3Alist=UNDECIDED&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
#     getBugList(v_url, "FIXR_UNKOWNUNDECIDED_order1")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=UNKNOWN&field.importance%3Alist=UNDECIDED&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
#     getBugList(v_url, "FIXR_UNKOWNUNDECIDED_order2")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "FIXR_CRITICAL")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
#     getBugList(v_url, "FIXR_CRITICAL_order1")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
#     getBugList(v_url, "FIXR_CRITICAL_order2")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "FIXR_HIGH")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
#     getBugList(v_url, "FIXR_HIGH_order1")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
#     getBugList(v_url, "FIXR_HIGH_order2")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "FIXR_Medium")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
#     getBugList(v_url, "FIXR_Medium_order1")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
#     getBugList(v_url, "FIXR_Medium_order2")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "ALL_ALL")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
#     getBugList(v_url, "ALL_ALL_order_id_1")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
#     getBugList(v_url, "ALL_ALL_order_id_2")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=status"
#     getBugList(v_url, "ALL_ALL_order_status_1")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-status"
#     getBugList(v_url, "ALL_ALL_order_status_2")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=UNDECIDED&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "ALL_undecided")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "ALL_CRITICAL")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "ALL_HIGH")
# except:
#     print("error")

# try:
#     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=MIDDLE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
#     getBugList(v_url, "ALL_MIDDLE")
# except:
#     print("error")

# fix releasedがデフォルトでは入っていない。デフォルトからの変更はfix releasedを含めただけ
# さすがに数が多すぎるので、18.04でWebのほうでフィルタリングしたものにする（これはやむなし）
# ubuntu oneにログインでかなりめんどい
# url = "https://bugs.launchpad.net/ubuntu/+bugs?field.tags_combinator=ANY&field.omit_dupes=on&field.has_patch.used=&assignee_option=any&field.has_no_blueprints=on&field.has_no_branches=on&field.affects_me.used=&field.omit_dupes.used=&field.has_no_package.used=&field.bug_commenter=&field.bug_reporter=&field.has_no_blueprints.used=&field.has_blueprints=on&field.assignee=&field.has_cve.used=&field.searchtext=18.04&field.subscriber=&field.has_branches.used=&field.has_branches=on&field.component-empty-marker=1&orderby=-importance&search=Search&field.structural_subscriber=&field.has_blueprints.used=&field.status_upstream-empty-marker=1&field.has_no_branches.used=&field.status=NEW&field.status=CONFIRMED&field.status=TRIAGED&field.status=INPROGRESS&field.status=FIXCOMMITTED&field.status=FIXRELEASED&field.status=INCOMPLETE_WITH_RESPONSE&field.status=INCOMPLETE_WITHOUT_RESPONSE&field.tag="

# url = "https://bugs.launchpad.net/ubuntu/?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"

# url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"

