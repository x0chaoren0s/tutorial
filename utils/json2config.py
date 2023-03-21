'''
从scrapy的SshServerWritingJsonPipeline保存的json中提取config url到conf文件
'''

import os, json
try:
    from common_tools import normalize_date
except:
    from utils.common_tools import normalize_date

class ConfigBuilder:
    def __init__(self, config_path) -> None:
        self.config_path = config_path
        self.json_folder = 'results/sshservers'
        self.datespan_region_configs = self._get_valid_configs_and_set_logins()

    def build(self):
        '''
        将self.datespan_region_configs的内容按conf格式写入self.config_path  
        '''
        with open(self.config_path, 'w') as fout:
            for datespan in self.datespan_region_configs:
                print(datespan, file=fout)
                for region in self.datespan_region_configs[datespan]:
                    for configurl in self.datespan_region_configs[datespan][region]:
                        print(configurl, file=fout)


    def _get_valid_configs_and_set_logins(self):
        '''
        查看所有json文件，查看max_logins仍大于now_logins的，
        按时间-地区返回它们的config，并更新其now_logins
        '''
        ret = dict() # {"# 2022-12-27 - 2023-01-04":{"France":["forward=.."]}}
        jsons = [f for f in os.listdir(self.json_folder) if f.endswith('.json')]
        for j in jsons:
            jpath = os.path.join(self.json_folder, j)
            with open(jpath, 'r') as fin:
                jdict = json.load(fin)
            jconfigs = jdict['configs']
            for config in jconfigs:
                if 'error_info' in config:
                    continue
                config.setdefault('max_logins', '1')
                config.setdefault('now_logins', '0')
                if int(config['now_logins']) >= int(config['max_logins']):
                    continue
                date_beg, date_end = config['date_span'].split('# ')[1].split(' - ') # '# 2023-03-21 - 2023-03-28',  "# 2023-03-21 - 2023-03-28 / 21:12:52"
                date_beg = normalize_date(date_beg, ["%Y-%m-%d", "%Y-%m-%d / %H:%M:%S"])
                date_end = normalize_date(date_end, ["%Y-%m-%d", "%Y-%m-%d / %H:%M:%S"])
                date_span = f'# {date_beg} - {date_end}'
                ret.setdefault(date_span, dict())
                ret[date_span].setdefault(config['region'], [])
                ret[date_span][config['region']].append(config['glider_config'])
                config['now_logins'] = f'{int(config["now_logins"])+1}'
            with open(jpath, 'w') as fout:
                json.dump(jdict, fout, indent=4)
        return ret
        

if __name__ == '__main__':
    configfile='momomo2/glider_test.conf'
    cb=ConfigBuilder(configfile)
    print(os.listdir(cb.json_folder))
    print(cb.datespan_region_configs)
    cb.build()