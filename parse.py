# -*- coding: utf-8 -*-
"""
Xiangya PsychTree 数据解析脚本
输入：本科.txt / 硕士.txt / 博士.txt（中南大学精神医学历届名单）
输出：data/xiangya-psychtree.json（结构化数据，供网页内嵌）
"""
import re, json, os, collections

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(_HERE, 'data', 'source')
OUT = os.path.join(_HERE, 'data', 'xiangya-psychtree.json')


def read_lines(path):
    raw = open(path, 'rb').read()
    for enc in ('utf-8', 'gbk', 'gb18030'):
        try:
            return raw.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'replace').splitlines()


def norm(s):
    """去除姓名/导师名内部的空白，保留汉字、点号、连字符等"""
    return re.sub(r'\s+', '', s)


def parse_bachelor(lines):
    """本科：* YYYY 年 块 + 纯姓名列表（姓名可能出现在标题行或后续行）"""
    blocks = []
    cur = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^\*\s*(\d{4})\s*年(.*)$', line)
        if m:
            cur = {'year': int(m.group(1)), 'names': []}
            blocks.append(cur)
            for tok in m.group(2).split():
                cur['names'].append(norm(tok))
            continue
        if cur is None:
            continue
        for tok in line.split():
            cur['names'].append(norm(tok))
    return blocks


def _add_entries(cur, text):
    """从文本中解析 姓名（导师1、导师2） 条目；无括号姓名也兜底保留"""
    spans = []
    for mm in re.finditer(
        r'([\u4e00-\u9fff]{1,12})\s*[（(]\s*([^）)]+?)\s*[）)]',
        text):
        name = norm(mm.group(1))
        mentors = [norm(x) for x in re.split(r'[、,，/]', mm.group(2)) if norm(x)]
        if not name:
            continue
        cur['students'].append({'name': name, 'mentors': mentors})
        spans.append((mm.start(), mm.end()))
    # 兜底：未被括号条目覆盖的姓名片段
    rest = ''
    pos = 0
    for s, e in sorted(spans):
        rest += text[pos:s] + ' ' * (e - s)
        pos = e
    rest += text[pos:]
    for tok in rest.split():
        if re.fullmatch(r'[\u4e00-\u9fff]{2,6}', tok):
            cur['students'].append({'name': norm(tok), 'mentors': []})


def parse_mentored(lines):
    """硕士/博士：* YYYY届/级 块 + 姓名（导师）条目
    注意：条目可能位于标题行（* 1978级	谢光荣（龚耀先）...）或后续行"""
    blocks = []
    cur = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^\*\s*(\d{4})\s*(届|级)(.*)$', line)
        if m:
            cur = {'year': int(m.group(1)), 'cohort': m.group(2), 'students': []}
            blocks.append(cur)
            if m.group(3).strip():
                _add_entries(cur, m.group(3))
            continue
        if cur is None:
            continue
        _add_entries(cur, line)
    return blocks


def dedupe_records(blocks):
    """同一学历内去重：姓名+年份+届别 完全相同则合并"""
    for b in blocks:
        seen = set()
        out = []
        if 'names' in b:
            for n in b['names']:
                if n not in seen:
                    seen.add(n)
                    out.append(n)
            b['names'] = out
        else:
            for s in b['students']:
                key = (s['name'], tuple(s['mentors']))
                if key not in seen:
                    seen.add(key)
                    out.append(s)
            b['students'] = out
    return blocks


def merge_same_name_same_year(blocks):
    """同年级同名合并（站点按姓名整合展示；同名可能为不同个体，页面有提示）"""
    for b in blocks:
        if 'names' in b:
            continue
        seen = {}
        out = []
        for s in b['students']:
            if s['name'] in seen:
                for mt in s['mentors']:
                    if mt not in seen[s['name']]['mentors']:
                        seen[s['name']]['mentors'].append(mt)
            else:
                seen[s['name']] = s
                out.append(s)
        b['students'] = out
    return blocks


def parse_psych(lines):
    """心理学录取名单：从整理明细.md 的表格解析（姓名|导师|学院|批次|来源|备注）
    标题行：### YYYY级 硕士（N 人）/ ### YYYY级 博士（N 人）
    返回 {'硕士': [blocks], '博士': [blocks]}"""
    out = {'硕士': [], '博士': []}
    cur = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        mh = re.match(r'^###\s*(\d{4})级\s*(硕士|博士)', line)
        if mh:
            cur = {'year': int(mh.group(1)), 'cohort': '级', 'students': []}
            out[mh.group(2)].append(cur)
            continue
        if re.match(r'^##\s', line):
            cur = None
            continue
        if cur is None:
            continue
        if line.startswith('|') and not line.startswith('|---'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) >= 2 and cells[0] and cells[0] != '姓名':
                name = norm(cells[0])
                mt = norm(cells[1])
                mentors = [] if (not mt or mt == '（无）' or mt == '(无)') else [mt]
                if name:
                    cur['students'].append({'name': name, 'mentors': mentors})
    for lev in out:
        out[lev] = dedupe_records(out[lev])
    return out


def parse_theses(lines):
    """CNKI 学位论文（20261008 导出，带学历标注）：
    导师行（2-4 汉字）+ 硕士/博士 区块 + [N]姓名.标题[D].中南大学,年份
    返回 [{'mentor','degree','student','year'}]，同 (导师,学历,学生,年份) 去重"""
    out = []
    cur_mentor = None
    cur_degree = None
    seen = set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line in ('硕士', '博士'):
            cur_degree = line
            continue
        mh = re.match(r'^([\u4e00-\u9fff]{2,4})$', line)
        if mh:
            cur_mentor = mh.group(1)
            cur_degree = None
            continue
        m = re.match(r'^\[\d+\]\s*([\u4e00-\u9fff]{2,4})\.', line)
        if m and cur_mentor and cur_degree:
            my = re.search(r'[,，](\d{4})[\.\s]', line)
            year = int(my.group(1)) if my else 0
            key = (cur_mentor, cur_degree, m.group(1), year)
            if key not in seen:
                seen.add(key)
                out.append({'mentor': cur_mentor, 'degree': cur_degree,
                            'student': m.group(1), 'year': year})
    return out


def cnki_blocks(theses, degree):
    """把 CNKI 学位论文学生按 学历+毕业年份（届）组织成块，供 merge_psych 并入"""
    by_year = collections.defaultdict(list)
    for r in theses:
        if r['degree'] == degree and r['year']:
            by_year[r['year']].append({'name': r['student'], 'mentors': [r['mentor']]})
    return [{'year': y, 'cohort': '届', 'students': by_year[y]} for y in sorted(by_year)]


def build_derived(all_records):
    """all_records: [{degree, year, cohort, name, mentors}]"""
    persons = collections.defaultdict(list)
    mentors = collections.defaultdict(list)
    for r in all_records:
        persons[r['name']].append({
            'degree': r['degree'], 'year': r['year'],
            'cohort': r.get('cohort', ''), 'mentors': r['mentors']
        })
        for mt in r['mentors']:
            mentors[mt].append({
                'student': r['name'], 'degree': r['degree'],
                'year': r['year'], 'cohort': r.get('cohort', '')
            })
    return persons, mentors


def merge_psych(target, psych_blocks):
    """把心理学名单按 姓名+年级 并入精神医学名单（同年级同名跳过，保留精神医学原条目）
    无对应年级块时新建块（cohort=级）"""
    idx = {b['year']: b for b in target}
    for pb in psych_blocks:
        blk = idx.get(pb['year'])
        if blk is None:
            blk = {'year': pb['year'], 'cohort': '级', 'students': []}
            target.append(blk)
            idx[pb['year']] = blk
        existing = {s['name'] for s in blk['students']}
        for s in pb['students']:
            if s['name'] not in existing:
                blk['students'].append(s)
                existing.add(s['name'])
    target.sort(key=lambda b: b['year'])
    return target


def main():
    bachelor = parse_bachelor(read_lines(os.path.join(BASE, '本科.txt')))
    master = parse_mentored(read_lines(os.path.join(BASE, '硕士.txt')))
    doctor = parse_mentored(read_lines(os.path.join(BASE, '博士.txt')))

    # 心理学与CNKI学位论文学生已并入 硕士.txt/博士.txt（data/source 仅保留三份名单）
    # 论文清单数据从上一版 JSON 保留（页面导师抽屉仍展示）
    _old = {}
    try:
        with open(OUT, encoding='utf-8') as _f:
            _old = json.load(_f)
    except Exception:
        pass
    psych = _old.get('psych', {'硕士': [], '博士': []})
    theses = _old.get('theses', [])

    bachelor = dedupe_records(bachelor)
    master = dedupe_records(master)
    doctor = dedupe_records(doctor)
    # 同年级同名合并（同名可能为不同个体，与站点姓名整合展示一致）
    master = merge_same_name_same_year(master)
    doctor = merge_same_name_same_year(doctor)

    # 心理学与CNKI学生已直接并入 硕士.txt/博士.txt 源名单，不再二次合并（避免同人跨级重复）
    # psych/theses 仅保留供页面其它展示（psych 不渲染、theses 用于导师论文抽屉）
    master = dedupe_records(master)
    doctor = dedupe_records(doctor)

    # 站点展示不收录 2026 年数据（源文件保留完整）
    master = [b for b in master if b['year'] != 2026]
    doctor = [b for b in doctor if b['year'] != 2026]

    all_records = []
    for b in bachelor:
        for n in b['names']:
            all_records.append({'degree': '本科', 'year': b['year'], 'cohort': '', 'name': n, 'mentors': []})
    for b in master:
        for s in b['students']:
            all_records.append({'degree': '硕士', 'year': b['year'], 'cohort': b['cohort'],
                                'name': s['name'], 'mentors': s['mentors']})
    for b in doctor:
        for s in b['students']:
            all_records.append({'degree': '博士', 'year': b['year'], 'cohort': b['cohort'],
                                'name': s['name'], 'mentors': s['mentors']})

    persons, mentors = build_derived(all_records)

    data = {
        'generated': '2026-10-02',
        'source': {'bachelor': '本科.txt', 'master': '硕士.txt', 'doctor': '博士.txt',
                   'psych': '心理学录取名单.txt', 'theses': '导师学位论文清单_CNKI导出_20261008.txt'},
        'bachelor': bachelor,
        'master': master,
        'doctor': doctor,
        'psych': psych,
        'theses': theses,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    # ---- 统计与质量检查 ----
    multi = {k: v for k, v in persons.items() if len({x['degree'] for x in v}) >= 2}
    print('== 基础统计 ==')
    print('本科块数:', len(bachelor), '记录数:', sum(len(b['names']) for b in bachelor))
    print('硕士块数:', len(master), '记录数:', sum(len(b['students']) for b in master))
    print('博士块数:', len(doctor), '记录数:', sum(len(b['students']) for b in doctor))
    print('心理硕士块数:', len(psych['硕士']), '记录数:', sum(len(b['students']) for b in psych['硕士']))
    print('心理博士块数:', len(psych['博士']), '记录数:', sum(len(b['students']) for b in psych['博士']))
    print('导师论文记录数:', len(theses))
    print('总记录数:', len(all_records))
    print('独立姓名数:', len(persons))
    print('导师数:', len(mentors))
    print('跨学历人物数:', len(multi))

    print('\n== 多学历人物样例（>=2学历，按出现次数排序）==')
    for k, v in sorted(multi.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:40]:
        tags = ' | '.join(f"{x['degree']}{x['year']}{x['cohort']}{('(' + '/'.join(x['mentors']) + ')') if x['mentors'] else ''}" for x in sorted(v, key=lambda x: x['year']))
        print(f'{k}: {tags}')

    print('\n== 可疑姓名（长度>4）==')
    for r in all_records:
        if len(r['name']) > 4:
            print(r['name'], r['degree'], r['year'])

    print('\n== 无导师条目（硕士/博士）==')
    for b in master + doctor:
        for s in b['students']:
            if not s['mentors']:
                print(s['name'], b['year'], b['cohort'])

    print('\n== 空年份块 ==')
    for label, blocks in (('本科', bachelor), ('硕士', master), ('博士', doctor)):
        for b in blocks:
            n = len(b['names']) if 'names' in b else len(b['students'])
            if n == 0:
                print(label, b['year'], b.get('cohort', ''))

    print('\n== 分块核对（年份/届别 → 人数）==')
    for label, blocks in (('本科', bachelor), ('硕士', master), ('博士', doctor)):
        counts = []
        for b in blocks:
            n = len(b['names']) if 'names' in b else len(b['students'])
            counts.append(f"{b['year']}{b.get('cohort','')}:{n}")
        print(label, '→', ', '.join(counts))

    print('\n== Top 导师（按学生记录数）==')
    for k, v in sorted(mentors.items(), key=lambda kv: -len(kv[1]))[:15]:
        print(k, len(v))

    print('\n输出:', OUT)


if __name__ == '__main__':
    main()
