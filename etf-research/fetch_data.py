from pathlib import Path
import requests, json, datetime, concurrent.futures, sys

ROOT = Path(__file__).parent
OUT = ROOT / 'sources'
OUT.mkdir(exist_ok=True)
URLS = {
 'krw_stooq':'https://stooq.com/q/d/l/?s=usdkrw&i=d&d1=20000101&d2=20261019',
 'krw_fred_text':'https://fred.stlouisfed.org/data/DEXKOUS.txt',
 'krw_fred':'https://fred.stlouisfed.org/graph/?id=DEXKOUS&cosd=1990-01-01&coed=2026-10-19&fq=Daily&format=csv',
 'krw_fred_csv':'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXKOUS&cosd=1990-01-01&coed=2026-10-19',
 'voo_actual_holdings':'https://investor.vanguard.com/irr/funds/profile/VOO-AdditionalFundData',
 'voo_common':'https://funds-web-components.cdn.web.vanguard.com/common-DJ-R-yUj.js',
 'voo_api':'https://api.vanguard.com/rs/gre/gra/1.7.0/datasets/VOO-AdditionalFundData.json',
 'voo_api2':'https://investor.vanguard.com/investment-products/etfs/profile/api/VOO-AdditionalFundData',
 'qqq_api_sector':'https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46090E103/weightedHoldings/fund?idType=cusip&breakdown=sector&productType=ETF',
 'qqq_api_performance':'https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46090E103/performance/standard?idType=cusip&performanceSubType=annualized&productType=ETF&performancePeriod=monthEnd',
 'voo_component':'https://funds-web-components.cdn.web.vanguard.com/portfolio-composition.js',
 'qqq_sa2':'https://www.slickcharts.com/nasdaq100',
 'voo_spdr':'https://www.ssga.com/us/en/individual/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx',
 'qqq_api_holdings':'https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46090E103/holdings/fund?idType=cusip&productType=ETF',
 'qqq_api_stats':'https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46090E103?expand=nav&idType=cusip&variationType=fundCharacteristics&productType=ETF',
 'qqq_api_details':'https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46090E103?expand=nav&idType=cusip&variationType=fundDetails&productType=ETF',
 'ixn_history':'https://www.ishares.com/us/products/239750/ishares-global-tech-etf/1522725744755.ajax?fileType=csv&fileName=IXN_holdings&dataType=fund&asOfDate=20100129',
 'ixn_download':'https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US&portfolioId=239750&component=fundDownload&userType=individual',
 'voo_sa':'https://stockanalysis.com/etf/voo/holdings/',
 'qqq_sa':'https://stockanalysis.com/etf/qqq/holdings/',
 'voo_vg_holdings':'https://investor.vanguard.com/investment-products/etfs/profile/voo#portfolio-composition',
 'xndx_fred':'https://fred.stlouisfed.org/graph/?g=1&cosd=1985-01-01&coed=2026-10-19&id=NASDAQXNDX',
 'ixn_page': 'https://www.ishares.com/us/products/239750/ishares-global-tech-etf',
 'ixn_holdings': 'https://www.ishares.com/us/products/239750/ishares-global-tech-etf/latest-holdings.csv',
 'qqq_page': 'https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html',
 'qqq_holdings': 'https://www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0?audienceType=Investor&ticker=QQQ',
 'voo_page': 'https://advisors.vanguard.com/investments/products/voo/vanguard-sp-500-etf',
 'voo_factsheet': 'https://fund-docs.vanguard.com/F0968.pdf',
 'ixn_factsheet': 'https://www.ishares.com/us/literature/fact-sheet/ixn-ishares-global-tech-etf-fund-fact-sheet-en-us.pdf',
 'qqq_factsheet': 'https://www.invesco.com/us-rest/contentdetail?contentId=3a48e01e98630410VgnVCM10000046f1bf0aRCRD',
 'ndx_factsheet':'https://indexes.nasdaqomx.com/docs/FS_NDX.pdf',
}
for s in ['IXN','QQQ','VOO','SPY','FSPTX','VFINX','TSM','ASML','2330.TW','ASML.AS','005930.KS','005935.KS','000660.KS','KRW=X','^NDX','^XNDX','^SP500TR','^GSPC','^IRX']:
 URLS['price_'+s.replace('^','').replace('.','_')] = 'https://query1.finance.yahoo.com/v8/finance/chart/'+requests.utils.quote(s,safe='')+'?period1=473385600&period2=1792540800&interval=1d&events=div%2Csplits'

def fetch(pair):
 k,u=pair
 try:
  r=requests.get(u,headers={'User-Agent':'Mozilla/5.0'},timeout=60)
  r.raise_for_status()
  ext='json' if k.startswith('price_') or r.content[:1] in (b'{',b'[') else ('csv' if 'holdings' in k and r.content[:10].lower().find(b'<')<0 else ('pdf' if 'factsheet' in k and r.content[:4]==b'%PDF' else 'html'))
  p=OUT/(k+'.'+ext);p.write_bytes(r.content)
  return {'key':k,'url':u,'file':p.name,'bytes':len(r.content),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 except Exception as e:return {'key':k,'url':u,'error':str(e)}

if __name__=='__main__':
 chosen=[(k,u) for k,u in URLS.items() if len(sys.argv)==1 or k in sys.argv[1:]]
 results=list(concurrent.futures.ThreadPoolExecutor(6).map(fetch,chosen))
 p=OUT/'fetch_log.json'
 old=json.loads(p.read_text()) if p.exists() else []
 old=[x for x in old if x['key'] not in dict(chosen)]
 p.write_text(json.dumps(old+results,indent=2))
 print(json.dumps(results,indent=2))
