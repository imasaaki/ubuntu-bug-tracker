import datetime
import requests
import re

# cache
page_target_ubuntu_true_dict = dict()
page_target_ubuntu_false_dict = dict()

def add_dict(a_dict, a_url, a_title):
    if a_url in a_dict:
        print('duplicate url:' + a_url)
        return
    a_dict[a_url] = a_title
    print('add url:' + a_url)

def getBugList(a_url, a_task, a_target_ubuntu_str, a_dt_ubuntu_target_major_version_release, a_dt_ubuntu_target_minor_version_release):
    print(a_url, a_task)
    url = a_url
    response = requests.get(url)
    response.encoding = response.apparent_encoding

    # 解析しやすいように改行とスペースを削除する
    noreturn_text = response.text.replace('\n', '').replace('\r', '').replace(' ', '')
    pattern_url = r'ahref="(https:\/\/bugs.launchpad.net\/ubuntu\/(\+source\/\S{0,50}\/|)\+bug\/\d+)"class='
    pattern_importance = r'<divclass="importanceimportance.{1,30}">(.{1,30})<\/div>'
    pattern_status = r'<divclass="statusstatus.{1,30}">(.{1,30})<\/div>'
    pattern_totalnumber = r'of(\d{1,10})results'
    pattern_lastupdate = r'"last_updated":"on(\d\d\d\d-\d\d-\d\d)"'

    matches_totalnumber = re.findall(pattern_totalnumber, noreturn_text)
    total_number = int(matches_totalnumber[0])

    with open('result.html', 'w', encoding='utf-8') as f:
        f.write(response.text)

    # Nextから次のページを取得するのは最初だけ、だんだんURLが長くなっていくので、線形に増えるいるわけではないので予測できず、その次からは数値だけを入れ替えていく
    pattern_nexturl = r'"next"href="(https:\S{0,5000})"id=\S{0,200}><strong>Next'
    matches_nexturl = re.findall(pattern_nexturl, noreturn_text)
    next_url = matches_nexturl[0]
    single_pange_number = 75

    # 除外リスト、+を追加しておく（エクセルでリストを作る都合上、＋を削除した経緯がある）
    excludes_set = set('+' + line.strip() for line in open('excludes.txt'))

    count = 0
    with open("output_" + a_task + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv', mode='a') as out_file:
        out_file.write('"url","module","title","importance","status","lastupdate"' + '\r\n')
        for i in range(0, int(total_number/single_pange_number) + 1):
            matches_url = re.findall(pattern_url, noreturn_text)
            matches_importance = re.findall(pattern_importance, noreturn_text)
            matches_status = re.findall(pattern_status, noreturn_text)
            matches_lastupdate = re.findall(pattern_lastupdate, noreturn_text)

            try:
                for j in range(len(matches_url)):

                    title = ""

                    is_target_ubuntu = False
                    dt_bug = datetime.datetime.strptime(matches_lastupdate[j], '%Y-%m-%d')

                    # major versionのrelease前のものは見ない
                    # minor versionのrelease少し前にクローズしたものは見ない
                    # 除外リストにあるものは見ない
                    if dt_bug > a_dt_ubuntu_target_major_version_release and (matches_status[j] != "FixReleased" or dt_bug > a_dt_ubuntu_target_minor_version_release) and (not (matches_url[j][1] in excludes_set)):
                        # 一度見たものはもう見ないようにする
                        if matches_url[j][0] in page_target_ubuntu_true_dict:
                            is_target_ubuntu = True
                            title = page_target_ubuntu_true_dict[matches_url[j][0]]
                            print('hit true cache: ' + matches_url[j][0])
                        elif matches_url[j][0] in page_target_ubuntu_false_dict:
                            is_target_ubuntu = False
                            title = page_target_ubuntu_false_dict[matches_url[j][0]]
                            print('hit false cache: ' + matches_url[j][0])
                        else:
                            print('no cache: ' + matches_url[j][0])
                            response_bugpage = requests.get(matches_url[j][0])
                            response_bugpage.encoding = response.apparent_encoding
                            pattern_title_in_sigle_page = r'<h1 id="edit-title">\n.*\n(.*)\n.*\n.*\n<\/h1>'
                            matches_title = re.findall(pattern_title_in_sigle_page, response_bugpage.text)
                            title = matches_title[0]
                            if a_target_ubuntu_str in response_bugpage.text:
                                is_target_ubuntu = True
                                add_dict(page_target_ubuntu_true_dict, matches_url[j][0], title)
                            else:
                                add_dict(page_target_ubuntu_false_dict, matches_url[j][0], title)
                                            
                        ## +sourceとバックスラッシュが、後工程で邪魔なので削除
                        # if len(matches_url[j][1]) > 0:
                        #    matches_url[j][1] = matches_url[j][1].replace("+source","").replace("/", "")
                        if is_target_ubuntu == True:
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
                # 継続させる
                print("loop error")

            url = next_url
            print(url) # debug

            response = requests.get(url)
            response.encoding = response.apparent_encoding
            noreturn_text = response.text.replace('\n', '').replace('\r', '').replace(' ', '')
            next_page = (i + 2) * single_pange_number
            next_url = re.sub(r'memo=\d+&amp;start=\d+', 'memo={}&amp;start={}'.format(next_page, next_page), next_url)
            print('count={}, i={}, next_page={}'.format(count, i, next_page)) # debug

def main():

    target_ubuntu_str = '18.04'
    # ubuntu 1804のリリース日(2018/4/26)の少し前
    dt_1804_release = datetime.datetime(2018, 4, 1)
    # ubuntu18.0.4リリース(2020/2/12)の少し前
    dt_180404_release = datetime.datetime(2020, 2, 1)
  
    # 補足：v_urlはlaunchpadのサイトでフィルタをかけた場合のURLをコピーしてくる
    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
        getBugList(v_url, "CRITICAL", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
        getBugList(v_url, "HIGH", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
        getBugList(v_url, "HIGH_order1", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
        getBugList(v_url, "HIGH_order2", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
        getBugList(v_url, "Medium", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
        getBugList(v_url, "Medium_order1", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
        getBugList(v_url, "Medium_order2", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    # try:
    #     v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=18.04&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
    #     getBugList(v_url, "Ubuntu1804")
    # except:
    #     print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
        getBugList(v_url, "FIXR_CRITICAL", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
        getBugList(v_url, "FIXR_CRITICAL_order1", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=CRITICAL&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
        getBugList(v_url, "FIXR_CRITICAL_order2", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
        getBugList(v_url, "FIXR_HIGH", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
        getBugList(v_url, "FIXR_HIGH_order1", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=HIGH&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
        getBugList(v_url, "FIXR_HIGH_order2", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
        getBugList(v_url, "FIXR_Medium", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
        getBugList(v_url, "FIXR_Medium_order1", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=MEDIUM&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
        getBugList(v_url, "FIXR_Medium_order2", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on"
        getBugList(v_url, "ALL_ALL", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=id"
        getBugList(v_url, "ALL_ALL_order_id_1", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-id"
        getBugList(v_url, "ALL_ALL_order_id_2", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=status"
        getBugList(v_url, "ALL_ALL_order_status_1", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

    try:
        v_url = "https://bugs.launchpad.net/ubuntu/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=INCOMPLETE_WITHOUT_RESPONSE&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.component-empty-marker=1&field.tag=&field.tags_combinator=ANY&field.status_upstream-empty-marker=1&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_no_package.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&orderby=-status"
        getBugList(v_url, "ALL_ALL_order_status_2", target_ubuntu_str, dt_1804_release, dt_180404_release)
    except:
        print("error")

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

if __name__ == "__main__":
    main()