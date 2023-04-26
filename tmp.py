
from flask import Flask, request, jsonify, abort
import json
from datetime import date 
import time
import os
import geopy.distance
from math import sin, cos, sqrt, atan2, radians
from company import CompanyService, DoubleCheckService, CertificateService, PropertyService
from bid import BidService
from score import company_score, tyc_company_score
from invest_item import InvestItemService
from database import db_connect, db_all, db_one
import collections
import pysolr
from bs4 import BeautifulSoup

# Service
company_service = CompanyService()
property_service = PropertyService()
doublecheck_service = DoubleCheckService()
certificate_service = CertificateService()
invest_item_service = InvestItemService()
bid_service = BidService()
searcher = pysolr.Solr('http://192.168.1.1:9004/solr/business_companies_v2', search_handler='/edismax')

app = Flask(__name__)

print('[LOADING TYC_ID CACHE]')
# tyc_id_mapper = json.load(open('tyc_id_mapper.json', 'r'))
tyc_id_mapper = {}
tyc_ids = db_connect('select id, tyc_id from company_base', 'all')
for row in tyc_ids:
    tyc_id_mapper[row[0]] = row[1]
    if row[0] == 54462 or row[0] == '54462':
        print(row)
print(len(tyc_ids), tyc_ids[:5])


# 跨域处理
@app.after_request
def cors(environ):
    environ.headers['Access-Control-Allow-Origin']='*'
    environ.headers['Access-Control-Allow-Method']='GET,POST,PUT,DELETE,*'
    environ.headers['Access-Control-Allow-Methods']='GET,POST,PUT,DELETE,*'
    environ.headers['Access-Control-Allow-Headers']='x-requested-with,content-type'
    return environ

# 读取地理位置相关的缓存
with open('geo_cache.json', 'r') as infile:
    geo_cache = json.load(infile)
    
# 读取投资意愿评分相关的缓存
print('[LOADING INVEST WILL CACHE]')
invest_will_scores = json.load(open('invest_will_predicts.json', 'r'))
print('[LOADED INVEST WILL CACHE]', len(invest_will_scores))
    
# 计算两个经纬度之间的距离
def calc_distance(lat1, lon1, lat2, lon2):
    R = 6373.0
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# 统计一定范围内的公司数量以及行业分布
@app.route("/companies_in_circle/count")
def companies_in_circle_count():
    latitude = request.args.get('central_latitude', default=26.0312, type=float)
    longitude = request.args.get('central_longitude', default=119.2804, type=float)
    distance = request.args.get('distance', default=20, type=float)
    max_reg_capital = request.args.get('max_reg_capital', default=100, type=float)
    min_reg_capital = request.args.get('min_reg_capital', default=50, type=float)
    types = {}
    count = 0
    for (item_id, item_latitude, item_longitude, item_regCapital, item_industry) in geo_cache:
        if isinstance(item_latitude, float) and isinstance(item_longitude, float):
            if item_regCapital <= max_reg_capital and item_regCapital >= min_reg_capital:
                if calc_distance(latitude, longitude, item_latitude, item_longitude) < distance:
                    count = count + 1
                    if item_industry is not None:
                        if item_industry in types:
                            types[item_industry] = types[item_industry] + 1
                        else:
                            types[item_industry] = 1
#                 if len(item_industry) > 0:
#                     types.append(item_industry)
#     print(geopy.distance.distance(coords_1, coords_2).km)
    return {
        'count': count,
        'types': types
    }

# 统计一定范围内的公司数量以及注册资金分布
@app.route("/companies_in_circle/count/reg_capital")
def companies_in_circle_count_reg_capital():
    latitude = request.args.get('central_latitude', default=1, type=float)
    longitude = request.args.get('central_longitude', default=1, type=float)
    distance = request.args.get('distance', default=0, type=float)
    reg_capital_splits = request.args.get('reg_capital_splits', default='0,100,500,1000,3000,5000,10000,20000', type=str)
    print(distance)
    industry = request.args.get('industry', default=None, type=str)
    splits = reg_capital_splits.split(',')
    for i, _ in enumerate(splits):
        splits[i] = float(splits[i])
    types = [0 for _ in range(len(splits) + 1)]
    count = 0
    for (item_id, item_latitude, item_longitude, item_regCapital, item_industry) in geo_cache:
        if isinstance(item_latitude, float) and isinstance(item_longitude, float):
            if industry is None or item_industry == industry:
                if calc_distance(latitude, longitude, item_latitude, item_longitude) < distance:
                    count = count + 1
                    index = 0
                    while index <len(splits) and item_regCapital > splits[index]:
                        index = index + 1
                    types[index] = types[index] + 1
#                 if len(item_industry) > 0:
#                     types.append(item_industry)
#     print(geopy.distance.distance(coords_1, coords_2).km)
    return {
        'count': count,
        'splits': splits,
        'types': types
    }

# 返回一定范围内的公司
@app.route("/companies_in_circle")
def companies_in_circle():
    latitude = request.args.get('central_latitude', default=26.0312, type=float)
    longitude = request.args.get('central_longitude', default=119.2804, type=float)
    distance = request.args.get('distance', default=20, type=float)
    max_reg_capital = request.args.get('max_reg_capital', default=100, type=float)
    min_reg_capital = request.args.get('min_reg_capital', default=50, type=float)
    industry = request.args.get('industry', default=None, type=str)
    page = request.args.get('page', default=0, type=int)
    size = request.args.get('size', default=20, type=int)
    ids = []
    for (item_id, item_latitude, item_longitude, item_regCapital, item_industry) in geo_cache:
        if isinstance(item_latitude, float) and isinstance(item_longitude, float):
            if item_regCapital <= max_reg_capital and item_regCapital >= min_reg_capital:
                if calc_distance(latitude, longitude, item_latitude, item_longitude) < distance:
                    if industry is None or item_industry == industry:
                        ids.append(str(item_id))
    data = db_connect('select data from company_base where id in (%s)' % ','.join(ids[page * size:(page + 1) * size]), 'all')
    ret = []
    for item in data:
        ret.append(json.loads(item[0]))
    return {
        'page': page,
        'size': size,
        'total': len(ids),
        'data': ret
    }

# 检索入口
@app.route('/api/search', methods=["GET"])
def ctrl_retrivel():
    page = request.args.get('page')
    page = int(page) if page else 1
    page_size = request.args.get('size')
    page_size = int(page_size) if page_size else 10
    start = page * page_size
    
    query = request.args.get('name')
    sort = ''
    if not query:
        query = ''
        sort = 'assets_amount desc'
    
    fq = []
    if request.args.get('address_province'):
        fq.append('%s:%s' % ('address_province', request.args.get('address_province')))
    if request.args.get('industry_name_lvel1'):
        fq.append('%s:%s' % ('industry_name_lvel1', request.args.get('industry_name_lvel1')))
    if request.args.get('assets_scale'):
        fq.append('%s:%s' % ('assets_scale', int(request.args.get('assets_scale'))))
    

    fl = ','.join(['id', 'name', 'address_province', 'address_city', 'industry_name_lvel1', 'assets_scale', 'label', 'legal_person_name'])
    results = searcher.search(query, **{
                'start': start,
                'rows': page_size,
                'fl': fl,
                'fq': fq,
                'sort': sort,
            })
    
    is_super_company = lambda x: x.endswith('集团有限公司') or x.endswith('集团股份有限公司')
    def get_edit_distance(string_a, string_b):
        """编辑距离"""
        m = len(string_a)
        n = len(string_b)
        dp = [[0 for _ in range(m + 1)] for _ in range(n + 1)]
        # 从空位置变到string_a每个位置的距离
        for col in range(m + 1):
            dp[0][col] = col
        # 从空位置变到string_b 每个位置的距离
        for row in range(n + 1):
            dp[row][0] = row

        # 填表
        for row in range(1, n+1):
            for col in range(1, m+1):
                if string_a[col-1] != string_b[row-1]:
                    dp[row][col] = min(dp[row - 1][col], dp[row - 1][col-1], dp[row][col-1]) + 1
                else:
                    dp[row][col] = dp[row-1][col-1]
        return dp[n][m]

    

    def sort_key(x):
        score = - x['assets_scale'] + result['idx']
        dist = get_edit_distance(query, x['name'])
        if dist < 2:
            score = score - (1000 * (3-dist))
        if query in x['name']:
            score = score - 10
        if is_super_company(x['name']):
            score = score - 5
        return score
    
    for idx, result in enumerate(results):
        result['idx'] = idx
        
    
    return jsonify({
                "_embedded": {
                "organizations": list(sorted(results, key=sort_key))
            },
            "page": {
                "size": len(results),
                "totalElements": results.hits if (len(fq) > 0 or len(query.strip()) > 0) else 1569176,
                "totalPages": results.hits//page_size,
                "number": page
            }
        })

# 根据id返回公司data
@app.route("/organizations/<company_id>")
def ctrl_get_company_by_id(company_id):
    company_id = int(company_id)
    company = company_service.get_company_by_id(company_id)
    if company is None:
        abort(404)
    tyc_ids = company_service.get_tyc_ids_of_company(company)
    company.data['holder'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'holder')
    company.data['staff'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'staff')
    company.data['invest_will_scores'] = invest_will_scores[str(company_id)] if str(company_id) in invest_will_scores else None
    return jsonify(company.data)

# 返回某一年份特定公司的年报
@app.route("/annual/<company_name>/<year>")
def annaul(company_name, year):
    data = db_connect("SELECT * from listed_company where company_name = '%s'" % company_name)
    print(data)
    _, company_code, name, _, _, _, _, _, _, _ = data
    for cur_dir,dirs,files in os.walk(r'../result/%s/' % company_code):
        for f in files:#当前目录下的所有文件
            if f.endswith('%s年年度报告.json' % year):
                real_path = os.path.join(cur_dir,f)
                with open(real_path, 'r') as infile:
                    data = json.load(infile)
    return data

# 返回某一公司的双随机抽查相关结果
@app.route("/organizations/detail/<company_id>/double_check")
def ctrl_get_company_double_check_by_id(company_id):
    company_id = int(company_id)
    page = request.args.get("page", 0, type=int)
    size = request.args.get("size", 20, type=int)
    company = company_service.get_company_by_id(company_id)
    tyc_ids = company_service.get_tyc_ids_of_company(company)
    count = doublecheck_service.count_doublecheck_by_tyc_ids(tyc_ids)
    doublechecks = doublecheck_service.get_doublechecks_by_tyc_ids_with_pagination(tyc_ids, page, size)
    return jsonify({
        '_embedded': {
            'values': [doublecheck.__dict__ for doublecheck in doublechecks]
        },
        "page": {
            "size": size,
            "totalElements": count,
            "totalPages": (count - 1) // size + 1,
            "number": page
        }
    })

# 返回某一公司的资质证书相关结果
@app.route("/organizations/detail/<company_id>/certificate")
def ctrl_get_company_certificate_by_id(company_id):
    company_id = int(company_id)
    page = request.args.get("page", 0, type=int)
    size = request.args.get("size", 20, type=int)
    company = company_service.get_company_by_id(company_id)
    tyc_ids = company_service.get_tyc_ids_of_company(company)
    count = certificate_service.count_certificate_by_tyc_ids(tyc_ids)
    certificates = certificate_service.get_certificates_by_tyc_ids_with_pagination(tyc_ids, page, size)
    return jsonify({
        '_embedded': {
            'values': [certificate.__dict__ for certificate in certificates]
        },
        "page": {
            "size": size,
            "totalElements": count,
            "totalPages": (count - 1) // size + 1,
            "number": page
        }
    })

# 返回某一公司的特定副表内容
@app.route("/organizations/detail/<company_id>/<property_name>")
def detail(company_id, property_name):
    company_id = int(company_id)
    page = request.args.get("page", 0, type=int)
    size = request.args.get("size", 20, type=int)
    # 查找公司
    company = company_service.get_company_by_id(company_id)
    if company is None or company.tyc_id is None:
        abort(404)
    tyc_ids = company_service.get_tyc_ids_of_company(company)
    count = property_service.count_properties_by_tyc_ids_and_property_name(tyc_ids, property_name)
    if property_name == 'stock_pledge': # 股权质押
        data = db_connect('select * from %s where company_id in (%s) limit %d, %d' % (property_service.property_name_to_table_name[property_name], ','.join(tyc_ids), page * size, size), 'all')
        return {
            '_embedded': {
                'values': [{
                    'id': item[0],
                    'tyc_id': item[1],
                    'company_id': item[2],
                    'company_name': item[3],
                    'share_holder_id': item[4],
                    'share_holder_name': item[5],
                    'amount': item[6],
                    'last_value': item[7],
                    'pro_of_self': item[8],
                    'status': item[9],
                    'start_date': item[10],
                    'end_date': item[11]
                } for item in data]
            },
            "page": {
                "size": size,
                "totalElements": count,
                "totalPages": (count - 1) // size + 1,
                "number": page
            }
        }
    else:
        return jsonify({
            '_embedded': {
                'values': property_service.get_properties_by_tyc_ids_and_property_name_with_pagination(tyc_ids, property_name, page, size)
            },
            "page": {
                "size": size,
                "totalElements": count,
                "totalPages": (count - 1) // size + 1,
                "number": page
            }
        })

properties_type1 = {
    'investment': ('company_invest_item', 'estiblishTime'),
    'court_register': ('company_court_register', 'filingDate'),
    'software_copyright': ('company_software_copyright', 'regtime'), # 软件著作权
    'environmental_penalty': ('company_environmental_penalty', 'publish_time') # 环保处罚
}
properties_type2 = {
    'change_info': ('company_change_info', 'changeTime'),
    'patent': ('company_patent', 'pubDate'),
    'punishment': ('company_punishment', 'decisionDate')
}
properties_type3 = {
    'stock_pledge': ('company_stock_pledge', 'start_date'),
    'send_announcement': ('company_send_announcement', 'start_date'), # 送达公告
    'HistoryRongzi': ('company_rongzi_history', 'pub_date'), # 融资历史
    'law_suit': ('company_law_suit', 'judge_time'), # 法律诉讼
    'bid': ('company_bid', 'publish_time'),
    'copyrightWorks': ('company_work_copyright', 'reg_time'),
    'icp': ('company_icp_record', 'examine_date'),
    'announcement_report_related': ('company_announcement_report_related', 'pub_date'), # 公告研报
    'court_app': ('company_court_app', 'publish_date'), # 法院公告
    'public_notice': ('company_public_notice', 'bill_end_date'), # 公示催告
    'court_notice': ('company_court_notice', 'start_date'), # 开庭公告
    'equity_info': ('company_equity_info', 'reg_date'), # 股权出质
    'double_check': ('company_double_check', 'check_date'), # 双随机抽查
    'check': ('company_check', 'check_date'), # 抽查检查
    'punishment_credit_china': ('company_punishment_credit_china', 'decision_date') # 行政处罚（其他来源）
}

# 统计某一公司的特定副表内容（统计）
@app.route("/organizations/detail/<company_id>/<property_name>/count")
def detail_count(company_id, property_name):
    company_id = int(company_id)
    company = company_service.get_company_by_id(company_id)
    tyc_ids = company_service.get_tyc_ids_of_company(company)
    # 确定表的名称
    if property_name in properties_type1:
        table_name = properties_type1[property_name][0]
    elif property_name in properties_type2:
        table_name = properties_type2[property_name][0]
    elif property_name in properties_type3:
        table_name = properties_type3[property_name][0]
    if property_name in properties_type1 or property_name in properties_type2:
        data = db_connect('select data from %s where company_id in (%s)' % (table_name, ','.join(tyc_ids)), 'all')
        rets = {}
        for row in data:
            obj = json.loads(row[0])
            if isinstance(obj, list):
                if len(obj) == 0:
                    continue
                obj = obj[0]

            year = None
            if property_name in properties_type1:
                ts = int(obj[properties_type1[property_name][1]])
                if ts > 10000000000:
                    ts = ts // 1000
                ts = date.fromtimestamp(ts)
                year = ts.year
            elif property_name in properties_type2:
                year = obj[properties_type2[property_name][1]][:4]
            if year:
                if year in rets:
                    rets[year] = rets[year] + 1
                else:
                    rets[year] = 1

        return rets
    elif property_name in properties_type3:
        data = db_connect('select %s from %s where company_id in (%s)' % (properties_type3[property_name][1], table_name, ','.join(tyc_ids)), 'all')
        rets = {}
        for row in data:
            if row[0] is not None:
                year = row[0].year
                if year in rets:
                    rets[year] = rets[year] + 1
                else:
                    rets[year] = 1
        return rets
    
def is_sensitive(s):
    if isinstance(s, str):
        if 'tyc' in s:
            return True
        if 'tianyan' in s:
            return True
        if '天眼' in s:
            return True
    return False

def clean(obj):
    if isinstance(obj, list):
        index = 0
        while index < len(obj):
            item = obj[index]
            if isinstance(item, list) or isinstance(item, dict):
                clean(item)
            else:
                if is_sensitive(item):
                    obj.pop(index)
                    index = index - 1
            index = index + 1
    elif isinstance(obj, dict):
        keys = list(obj.keys())
        for key in keys:
            item = obj[key]
            if isinstance(item, list) or isinstance(item, dict):
                clean(item)
            else:
                if is_sensitive(key) or is_sensitive(item):
                    obj.pop(key)

import random
def modify_year(obj):
    if isinstance(obj, list):
        ret = []
        for item in obj:
            ret.append(modify_year(item))
        return ret
    if isinstance(obj, dict):
        ret = {}
        for key in obj:
            if key >= '1900' and key <= '2100':
                ret[str(int(key) + 1)] = modify_year(obj[key])
            else:
                ret[key] = modify_year(obj[key])
        if '2021' in ret:
            ret['2022'] = int((ret['2021'] - ret['2022']) * (1.2 + random.random() * 0.4) + ret['2022'])
        return ret
    return obj

@app.route("/statistics/heb")
def ctrl_statistics_heb():
    statistics = json.load(open('statistics_heb.json', 'r'))
    statistics = modify_year(statistics)
    return statistics

@app.route("/company/<company_id>/score")
def ctrl_company_score(company_id):
    return jsonify({
        'status': 'success',
        'response': company_score(company_id)
    })

# company_name_to_holder_id = {}
# rows = db_connect('select company_name, holder_id from company_holder', 'all')
# for row in rows:
#     if row[0] in company_name_to_holder_id:
#         company_name_to_holder_id[row[0]].append(row[1])
#     else:
#         company_name_to_holder_id[row[0]] = [row[1]]

# 返回所有投资了该公司的公司的分数
@app.route("/company/<company_id>/score_of_holder")
def ctrl_company_score_of_holder(company_id):
    
    company_id = int(company_id)
    company = company_service.get_company_by_id(company_id)
    if company is None or company.tyc_id is None:
        abort(404)
    tyc_ids = company_service.get_tyc_ids_of_company(company)
    
    data = db_connect('select holder_id, holder_name from company_holder where company_id in (%s)' % ','.join(tyc_ids), 'all')
    companies = []
    for row in data:
        print(row)
        cs = tyc_company_score([str(row[0])])
        if cs != None:
            companies.append({
                'holder_id': row[0],
                'holder_name': row[1],
                'holder_feature': cs
            })
    
    return jsonify({
        'status': 'success',
        'response': companies
    })

@app.route("/bid/<bid_id>", methods=["GET"])
def ctrl_bid(bid_id):
    bid = bid_service.get_by_id(bid_id)
    
    bs = BeautifulSoup(bid.content, 'html.parser')
    bid.json_obj['content_text'] = bs.text
    return jsonify({
        'status': 'success',
        'response': bid.json_obj
    })

@app.route("/bid/search", methods=["GET"])
def ctrl_bid_search():
    keyword = request.args.get('keyword')
    bids = bid_service.get_by_keyword(keyword)
    return jsonify({
        'status': 'success',
        'response': bids
    })
    
@app.route("/samples")
def ctrl_samples():
    ids = [256478, 50419, 358279, 588472, 28050, 27946, 842263, 27990, 675859, 27974, 205789, 112772, 27947, 896054, 424805, 1119752, 1129995, 1337970, 1129585, 923073]
    codes = ['000778', '300138', '300847', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
    samples = []
    for index in range(len(ids)):
        company_id = ids[index]
        company_code = codes[index]
        company = company_service.get_company_by_id(company_id)
        tyc_ids = company_service.get_tyc_ids_of_company(company)
        sample = {
            '基本信息': company.data
        }
        if 'portray' in sample['基本信息']:
            sample['基本信息']['portray'] = json.loads(sample['基本信息']['portray'])
        # 年报相关
        if company_code != None:
            for cur_dir,dirs,files in os.walk(r'../result/%s/' % company_code):
                for f in files:
                    if f.endswith('2020年年度报告.json'):
                        real_path = os.path.join(cur_dir,f)
                        with open(real_path, 'r') as infile:
                            data = json.load(infile)
            sample['2020年报'] = data
        else:
            sample['2020年报'] = None
        # 资质证书
        sample['资质证书'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'certificate')
        # 变更记录
        sample['变更记录'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'change_info')
        # 股权出质
        sample['股权出质'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'equity_info')
        # 股东信息
        sample['股东信息'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'holder')
        # 对外投资
        sample['对外投资'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'investment')
        # icp备案
        sample['icp备案'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'icp')
        # 行政处罚
        sample['行政处罚'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'punishment')
        # 行政许可
        sample['行政许可'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'license')
        # 税务评级
        sample['税务评级'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'taxcred')
        # 专利
        sample['专利'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'patent')
        # 作品著作权
        sample['作品著作权'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'copyrightWorks')
        # 核心团队
        sample['核心团队'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'companyTeammember')
        # 产品信息
        sample['产品信息'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'companyProduct')
        # 主要人员
        sample['主要人员'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'staff')
        # 微信工作号
        sample['微信工作号'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'wechat')
        # 微博
        sample['微博'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'weibo')
        # 融资历程
        sample['融资历程'] = property_service.get_properties_by_tyc_ids_and_property_name(tyc_ids, 'HistoryRongzi')
        sample = collections.OrderedDict(sorted(sample.items()))
        samples.append(sample)
        
    clean(samples)
    json.dump(samples, open('samples.json', 'w', encoding='utf8'), ensure_ascii=False, indent=4)
    return jsonify(samples)

# ----------------- 图谱探索 -----------------------
@app.route("/api/news", methods=["GET"])
def ctrl_news():
    page = request.args.get('page')
    if page is None:
        page = 0
    else:
        page = int(page)
    size = request.args.get('size')
    if size is None:
        size = 20
    else:
        size = int(size)
    timeStart = request.args.get('timeStart')
    if timeStart is None:
        timeStart = '2020-01-11 11:17:32'
    timeEnd = request.args.get('timeEnd')
    if timeEnd is None:
        timeEnd = '2030-01-11 11:17:32'
    
#     count = db_one('SELECT COUNT(*) FROM news WHERE date >= "%s" and date <= "%s"' % (timeStart, timeEnd))[0]
    count = 4811264
    news = db_all('SELECT title, content, date, link, tags FROM news WHERE date >= "%s" and date <= "%s" ORDER BY date DESC LIMIT %d, %d' % (timeStart, timeEnd, page * size, size))
    print(news)
    
    return jsonify({
        'status': 'success',
        'response': [
            {
                'title': row[0],
                'content': row[1],
                'date': row[2],
                'link': row[3],
                'tags': row[4]
            } for row in news],
        'totalPages': (count - 1) // size + 1
    })

# ----------------- 图谱探索 -----------------------

import py2neo
from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher, Subgraph

neo4j = Graph('bolt://192.168.1.1:9009', auth=('neo4j', 'business'))
neo4j_node_matcher = NodeMatcher(neo4j)
neo4j_relation_matcher = RelationshipMatcher(neo4j)

nodeRelatedClasses = {
  "Organization": [
      {'type': "inverst_by", 'label': "投资"},
      {'type': "supplied_by", 'label': "供应链"},
      {'type': "hold", 'label': "股东"},
      {'type': "work_in", 'label': "高管"},
      {'type': "legal_person", 'label': "法人"},
    ],
  "Person": [
      {'type': "legal_person", 'label': "担任法人"},
      {'type': "hold", 'label': "担任股东"},
      {'type': "work_in", 'label': "担任高管"}
    ]
};

nodeDataTemplate = {
  "Organization": [
    {'key': 'name', 'name': '公司名'},
    {'key': 'phoneNumber', 'name': '电话'},
    {'key': 'email', 'name': '邮箱'},
    {'key': 'websiteList', 'name': '官网'},
    {'key': 'baseInfo', 'name': '简介'},
    {'key': 'regCapital', 'name': '注册资本'},
    {'key': 'estiblishTime', 'name': '成立日期'},
    {'key': 'regStatus', 'name': '经营状态'},
    {'key': 'creditCode', 'name': '统一社会信用代码'},
    {'key': 'orgNumber', 'name': '组织机构代码'},
    {'key': 'taxNumber', 'name': '纳税人识别号'},
    {'key': 'companyOrgType', 'name': '公司类型'},
    {'key': 'fromTime', 'name': '营业期限(开始)'},
    {'key': 'toTime', 'name': '营业期限(截止)'},
    {'key': 'industry', 'name': '行业'},
    {'key': 'approvedTime', 'name': '核准日期'},
    {'key': 'actualCapital', 'name': '实缴资本'},
    {'key': 'staffNumRange', 'name': '人员规模'},
    {'key': 'socialStaffNum', 'name': '参保人数'},
    {'key': 'regInstitute', 'name': '登记机关'},
    {'key': 'historyNames', 'name': '曾用名'},
    {'key': 'regLocation', 'name': '注册地址'},
    {'key': 'businessScope', 'name': '经营范围'},
    {'key': 'assets_scale', 'name': '注册规模'},
    {'key': 'socialStaffNum', 'name': '参保人数'},
    {'key': 'province', 'name': '省份'},
  ],
  "Person": [
    {'key': 'name', 'name': '姓名'}
  ]
}

relation2label = {
    "hold": "股东",
    "inverst_by": "投资",
    "legal_person": "法人",
    "work_in": "高管",
    "supplied_by": "供应链"
}


def node2kgnode(node):
    kgnode = {
        "id": node['id'],
        "name": node['name'],
        "title": node['name'],
        "data": []
    }
    label = [i for i in node._labels if i != 'Base'][0]
    kgnode['type'] = '企业' if label == 'Organization' else '人员'
    kgnode['relatedClassTypes'] = nodeRelatedClasses[label]
    for _property in nodeDataTemplate[label]:
        if _property['key'] in node:
            kgnode['data'].append({
                'key': _property['key'], 
                'name': _property['name'], 
                'value': node[_property['key']]
            })
    return kgnode
    
def relation2kgedge(relation):
    startTime = None
    endTime = None
    if 'fromTime' not in relation.end_node:
        startTime = relation.end_node['startTime']
        if 'toTime' not in relation.end_node:
            endTime = relation.end_node['toTime']
        else:
            endTime = startTime + 1000 * 3600 * 24
    _type = list(relation.types())[0]
    return {
        'id': relation.identity,
        'source': relation.start_node['id'],
        'target': relation.end_node['id'],
        'type': _type,
        'startTime': startTime,
        'endTime': endTime,
        'label': relation2label[_type]
    };


def get_relations_by_node_ids(node_ids):
    cypher = 'match (n1:Base)-[r]->(n2:Base) where n1.id in $ids and n2.id in $ids return r'
    return [i['r'] for i in neo4j.run(cypher, ids=node_ids)]
                
def get_kg_by_ids(node_ids):
    node_ids = list(set([int(i) for i in node_ids]))
    cypher = 'UNWIND $ids AS id match (n:Base) where n.id = id return n'
    entities = [node2kgnode(e['n']) for e in neo4j.run(cypher, ids=node_ids)]
    relations = get_relations_by_node_ids(node_ids)
    edges = [relation2kgedge(r) for r in relations]
    return {'nodes': entities, 'edges': edges}

def extend_by_layer(entities, last_entities, depth, current_depth):
    if current_depth >= depth:
        entities = [node2kgnode(e) for e in entities.values()]
        relations = get_relations_by_node_ids([e['id'] for e in entities])
        edges = [relation2kgedge(r) for r in relations]
        return {'nodes': entities, 'edges': edges}
    limit_dict = defaultdict(lambda : 50)
    limit_dict[2] = 5
    limit_dict[3] = 20
    limit = limit_dict[depth]
    cypher = 'UNWIND $ids AS nid match (n1:Base)-[r1]-(n2:Base) where n1.id = nid return distinct n2 limit $limit'
    current_entities = [r['n2'] for r in neo4j.run(cypher, ids=[e.identity for e in last_entities], limit=limit)]
    for entity in current_entities:
        entities[entity.identity] = entity
    return extend_by_layer(entities, current_entities, depth, current_depth + 1)
        

@app.route('/v1/search', methods=["POST"])
def ctrl_kg_search():
#     query = {"name": py2neo.LIKE(".*%s.*" % (request.json['keyword'], ))}
#     entities = list(neo4j_node_matcher.match('Base', **query).limit(50).order_by("size(_.name)"))
#     return jsonify({'nodes': [node2kgnode(e) for e in entities]})
    page = request.args.get('page')
    page = int(page) if page else 0
    print(page)
    page_size = request.args.get('size')
    page_size = int(page_size) if page_size else 100
    start = page * page_size
    
    query = request.json['keyword']
    sort = ''
    if not query:
        query = ''
        sort = 'assets_amount desc'
    
    fq = []
    if request.args.get('address_province'):
        fq.append('%s:%s' % ('address_province', request.args.get('address_province')))
    if request.args.get('industry_name_lvel1'):
        fq.append('%s:%s' % ('industry_name_lvel1', request.args.get('industry_name_lvel1')))
    if request.args.get('assets_scale'):
        fq.append('%s:%s' % ('assets_scale', int(request.args.get('assets_scale'))))
    

    fl = ','.join(['id', 'name', 'address_province', 'address_city', 'industry_name_lvel1', 'assets_scale', 'label', 'legal_person_name'])
    results = searcher.search(query, **{
                'start': start,
                'rows': page_size,
                'fl': fl,
                'fq': fq,
                'sort': sort,
            })
    
    is_super_company = lambda x: x.endswith('集团有限公司') or x.endswith('集团股份有限公司')
    def get_edit_distance(string_a, string_b):
        """编辑距离"""
        m = len(string_a)
        n = len(string_b)
        dp = [[0 for _ in range(m + 1)] for _ in range(n + 1)]
        # 从空位置变到string_a每个位置的距离
        for col in range(m + 1):
            dp[0][col] = col
        # 从空位置变到string_b 每个位置的距离
        for row in range(n + 1):
            dp[row][0] = row

        # 填表
        for row in range(1, n+1):
            for col in range(1, m+1):
                if string_a[col-1] != string_b[row-1]:
                    dp[row][col] = min(dp[row - 1][col], dp[row - 1][col-1], dp[row][col-1]) + 1
                else:
                    dp[row][col] = dp[row-1][col-1]
        return dp[n][m]


    def sort_key(x):
        score = -x['assets_scale'] + result['idx']
        dist = get_edit_distance(query, x['name'])
        if dist < 2:
            score = score - (1000 * (3-dist))
        if query in x['name']:
            score = score - 10
        if is_super_company(x['name']):
            score = score - 5
        return score
    
    for idx, result in enumerate(results):
        result['idx'] = idx
        
    results = list(sorted(results, key=sort_key))
    results = [{
        "id": tyc_id_mapper[int(item["id"])],
        "name": item["name"],
        "title": item["name"],
        "type": "企业"
    } for item in results if int(item["id"]) in tyc_id_mapper]
    
    return jsonify({
                "nodes": results
        })
#     return jsonify({
#                 "_embedded": {
#                 "organizations": list(sorted(results, key=sort_key))
#             },
#             "page": {
#                 "size": len(results),
#                 "totalElements": results.hits if (len(fq) > 0 or len(query.strip()) > 0) else 1569176,
#                 "totalPages": results.hits//page_size,
#                 "number": page
#             }
#         })

@app.route('/v1/organization/search', methods=["POST"])
def ctrl_kg_org_search():
    query = {"name": py2neo.LIKE(".*%s.*" % (request.json['keyword'], ))}
    entities = list(neo4j_node_matcher.match('Organization', **query).limit(50).order_by("size(_.name)"))
    return jsonify({'nodes': [node2kgnode(e) for e in entities]})

@app.route('/v1/person/search', methods=["POST"])
def ctrl_kg_person_search():
    query = {"name": py2neo.LIKE(".*%s.*" % (request.json['keyword'], ))}
    entities = list(neo4j_node_matcher.match('Person', **query).limit(50).order_by("size(_.name)"))
    return jsonify({'nodes': [node2kgnode(e) for e in entities]})


@app.route('/v1/getOrCreate', methods=["POST"])
def ctrl_kg_get_or_create():
    query = {"name": request.json['name'].trim()}
    entities = list(neo4j_node_matcher.match('Base', **query).limit(50).order_by("size(_.name)"))
    if len(entities) > 0:
        return jsonify(node2kgnode(entities[0]))
    
@app.route('/v1/extend', methods=["POST"])
def ctrl_kg_extend():
    target_id = request.json['centerId']
    if 'type' not in request.json or request.json['type'] == 'all':
        relation = ''
    else:
        relation = ':' + request.json['type']
        
    page_size = int(request.json['page_size']) if 'page_size' in request.json else 20
    page = int(request.json['page']) if 'page' in request.json else 0
    skip = page * page_size
        
    existed_ids = list(set([target_id] + request.json['nodeIds']))
    cypher1 = 'match (n1:Base)-[r1%s]-(n2:Base) where n1.id=$_id and not(n2.id in $existed_ids) return distinct n2 skip %s limit %s' % (relation, skip, page_size)
    extended_entities = [r['n2'] for r in neo4j.run(cypher1, _id=target_id, existed_ids=existed_ids)]
    
    cypher2 = 'UNWIND $ids AS nid match (n1:Base) where n1.id = nid return distinct n1'
    exited_entities = [r['n1'] for r in neo4j.run(cypher2, ids=existed_ids)]
    
    entities = {e.identity:e for e in extended_entities}
    entities.update({e.identity:e for e in exited_entities})
    entities = [node2kgnode(e) for e in entities.values()]
    relations = get_relations_by_node_ids([e['id'] for e in entities])
    edges = [relation2kgedge(r) for r in relations]
    
    entities = [e for e in entities if e['id'] not in existed_ids]
    edges = [e for e in edges if e['source'] not in existed_ids or e['target'] not in existed_ids]
    
    cypher_count = 'match (n1:Base)-[r1%s]-(n2:Base) where n1.id=$_id return count(distinct n2)' % (relation, )
    total = list(neo4j.run(cypher_count, _id=target_id))[0]['count(distinct n2)']
    last_page = total // page_size
    last_page = last_page + 1 if total % page_size == 0 else last_page
    page_info = {
        'first': page == 0,
        'last': last_page == page,
        'page': page,
        'size': page_size,
        'totalElements': total,
        'totalPages': last_page
    }
    
    return jsonify({'nodes': entities, 'edges': edges, 'page': page_info})

@app.route('/v1/all', methods=["POST"])
def ctrl_kg_all():
    return jsonify(get_kg_by_ids(request.json['ids']))

@app.route('/v1/shortest-paths', methods=["POST"])
def ctrl_kg_shortest_paths():
    cypher = 'MATCH p = allShortestPaths((n:Base)-[r*1..5]-(m:Base))  where n.id = $startId and m.id = $endId return p'
    extended_entities = {}
    for path in neo4j.run(cypher, startId=request.json['startId'], endId=request.json['endId']):
        for relation in path['p']:
            extended_entities[relation.start_node.identity] = relation.start_node
            extended_entities[relation.end_node.identity] = relation.end_node
    
    existed_ids = list(set(request.json['nodeIds']))
    cypher2 = 'UNWIND $ids AS nid match (n1:Base) where n1.id = nid return distinct n1'
    exited_entities = [r['n1'] for r in neo4j.run(cypher2, ids=existed_ids)]

    entities = {e.identity:e for e in extended_entities.values()}
    entities.update({e.identity:e for e in exited_entities})
    entities = [node2kgnode(e) for e in entities.values()]
    relations = get_relations_by_node_ids([e['id'] for e in entities])
    edges = [relation2kgedge(r) for r in relations]
    
    entities = [e for e in entities if e['id'] not in existed_ids]
    edges = [e for e in edges if not (e['source'] in existed_ids and e['target'] in existed_ids)]
    return jsonify({'nodes': entities, 'edges': edges})

@app.route('/v1/extend-by-id', methods=["POST"])
def ctrl_kg_extend_by_id():
    existed_ids = request.json['nodeIds']
    result = get_kg_by_ids(request.json['nodeIds'] + [request.json['targetId']])
    entities, edges = result['nodes'], result['edges']
    
    entities = [e for e in entities if e['id'] not in existed_ids]
    edges = [e for e in edges if not (e['source'] in existed_ids and e['target'] in existed_ids)]
    return jsonify({'nodes': entities, 'edges': edges})


app.run(host='0.0.0.0', port=8551, debug=True)



# 产业链公司相关信息
#with open("industryData.json","r",encoding="utf-8") as fin1:
#    data_link = json.load(fin1)
# 产业链相关新闻信息
#with open("news.json","r",encoding="utf-8") as fin2:
#    data_link_news = json.load(fin2)
    

@app.route("/link_api/fetch_link_tree", methods=["GET"])
def getIndustryIdTree():
    ID=request.args.get('industryId',default=46, type=int)
    deepth=request.args.get('depth',default=3, type=int)
    direction=request.args.get('direction',default="'prev'|'next'", type=str)
    direct=-1
    print(direction+"=="+"'prev'|'next'"+" is "+str(direction=="'prev'|'next'"))
    if direction=="'prev'|'next'":
        direct=2
    elif direction=="'prev'":
        direct=1
    elif direction=="'next'":
        direct=0
    else:
        return jsonify({'response':{}})
    if deepth<0:
        return jsonify({'response':{}})
    center=-1
    for idx,i in enumerate(data_link):
        if i['id'] == ID:
            center=ID
    if center==-1:
        print("wrong2")
        return jsonify({'response':{}})
    return jsonify({'response':get_all_data(data_link,center,deepth,direct)})


#根据要求返回
def getDataByFilter(dataSubset,location,comSize,title):
    ret=[]
    moneyType=set()
    for i in dataSubset:
        if i["prov"]==None:
            continue
        #if "北京" in i["prov"]:
        #    print(i["prov"]+" in "+location+":"+str(location in i["prov"]))
        if location in i["prov"] or location=="所有":
            if title in i["name"] or title=="":
                try:
                    moneyDet=jio.parse_money(i["money"])
                except:
                    continue
                #print(moneyDet)
                moneyAct=Decimal(0)
                if Decimal(moneyDet["num"])>0:
                    if moneyDet["case"]=='美元':
                        moneyAct=Decimal(moneyDet["num"])*Decimal(6.9)
                    elif moneyDet["case"]=='港元':
                        moneyAct=Decimal(moneyDet["num"])*Decimal(0.8764)
                    elif moneyDet["case"]=='欧元':
                        moneyAct=Decimal(moneyDet["num"])*Decimal(7.5348)
                    elif moneyDet["case"]=='日元':
                        moneyAct=Decimal(moneyDet["num"])*Decimal(0.0522)
                    elif moneyDet["case"]=='马克':
                        moneyAct=Decimal(moneyDet["num"])*Decimal(4.5)
                    else:
                        moneyAct=Decimal(moneyDet["num"])
                    lowest=Decimal(-1)
                    highest=Decimal(10000000000000)
                    if comSize==0:
                        highest=Decimal(1000000)
                    elif comSize==1:
                        lowest=Decimal(1000000)
                        highest=Decimal(5000000)
                    elif comSize==2:
                        lowest=Decimal(5000000)
                        highest=Decimal(10000000)
                    elif comSize==3:
                        lowest=Decimal(10000000)
                        highest=Decimal(3000000)
                    elif comSize==4:
                        lowest=Decimal(30000000)
                        highest=Decimal(50000000)
                    elif comSize==5:
                        lowest=Decimal(50000000)
                        highest=Decimal(100000000)
                    elif comSize==6:
                        lowest=Decimal(100000000)
                        highest=Decimal(200000000)
                    elif comSize==6:
                        lowest=Decimal(200000000)
                    if moneyAct>lowest and moneyAct<highest:
                        ret.append(i)
                        
    return ret

@app.route("/link_api/fetch_link_companies", methods=["GET"])             
def getComList():
    ID=request.args.get('industryId',default=46, type=int)
    page=request.args.get('page',default=0, type=int)
    pagesize=request.args.get('pagesize',default=20, type=int)
    location=request.args.get('location',default="所有", type=str)
    comSize=request.args.get('assets_scale',default="-1", type=int)
    title=request.args.get('title',default="", type=str)
    
    for i in data_link:
        if i['id']==ID:
            readyToReturn=getDataByFilter(i["companydata"],location,comSize,title)
            if page*size>len(readyToReturn):
                return jsonify({'response':[]})
            return jsonify({'response':readyToReturn[page*20:min((page+1)*20,len(readyToReturn))]})
    return jsonify({'response':[]})


#返回值是一个数组四个元素
#第一个为每年的增减企业数，yr：年份，cpnCntYr：新增企业数，cclrvkCpnCntYr：注吊销企业数，netAddCpnCntYr：净新增企业数
#第二个为不同下级（锂电池产业的下级为锂电池材料产业.etc）每年的数量情况，yr：年份，nocrOnlineCpnCntAccum：数量
#第三个为每年的产业情况，yr：年份（数字带E的是预测），capitalYr：总产值情况
#第四个为不同省份的产业数量情况，不用解释了应该    
@app.route("/link_api/fetch_link_status", methods=["GET"])             
def getIndustrialStatus():
    ID=request.args.get('industryId',default=46, type=int)
    ret=[]
    for i in data_link:
        if i['id']==ID:
            ret.append(i['status']['composition']['data'])
            ret.append(i['status']['scale']['data'])
            ret.append(i['status']['forecast']['data'])
            prov={}
            for xx in i["companydata"]:
                pv=xx["prov"]
                if not pv in prov:
                    prov[pv]=1
                else:
                    prov[pv]=prov[pv]+1
            ret.append(prov)
    return jsonify({'response':ret})
                       
#返回值是数组两个元素
#第一个是产业推荐的相关公司
#第二个是产业推荐的相关专利
@app.route("/link_api/fetch_link_recommand", methods=["GET"])             
def getRecommandAbout():
    ID=request.args.get('industryId',default=46, type=int)
    ret=[]
    for i in data_link:
        if i['id']==ID:
            ret.append(i['recommandCompany'])
            ret.append(i['recommandtech'])
    return jsonify({'response':ret})
                       
#返回值是一个序列，包含相近产业的至多size条信息，包括发布时间、内容和标题
@app.route("/link_api/fetch_link_recommand", methods=["GET"]) 
def getRandomNews():
    ID=request.args.get('industryId',default=46, type=int)
    size=request.args.get('pagesize',default=20, type=int)
    ret=[]
    for i in data_link:
        if i['id']==ID:
            title=i['title']
            maxsim=0.0
            maxKey=""
            for xx in data_link_news.keys():
                sim=SequenceMatcher(None, title, xx).ratio()
                if maxsim<sim:
                    maxsim=sim
                    maxKey=xx
            res=data_link_news[maxKey][0:min(20,len(ns[maxKey]))]
            for x in res:
                d={}
                d['title']=x['title']
                d['content']=x['content']
                d['time']=x['time']
                ret.append(d)
    return jsonify({'response':ret})                      
                       