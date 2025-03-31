from dlisio import dlis
import dlisio

f = dlis.load('/home/houtj/projects/dlis_mcp_server/sample/sample toc.dlis')



def get_attributes(obj):
    return [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith('__')]

def get_channel(f, filename, framename, channelname):
    for lf in f:
        if lf.fileheader.attic['ID'].value[0].strip() != filename: continue
        for frame in lf.frames:
            if frame.name.strip() != framename: continue
            for channel in frame.channels:
                if channel.name.strip() != channelname: continue
                return channel
    return None

channel = get_channel(f, 'ConCu_R01_ReamDown010_PDX5_475_PERISCOPE_475_IMP_475', 'SONICSCOPE', 'AMP_CSG_TOC')
print(channel.curves())


def get_meta(f):
    meta_attr_list = [
            'axes',
            'calibrations',
            'channels',
            'coefficients',
            'comments',
            'computations',
            'equipments',
            'frames',
            'groups',
            'longnames',
            'measurements',
            'messages',
            'origins',
            'parameters',
            'paths',
            'processes',
            'splices',
            'tools',
            'wellrefs',
            'zones',]
    summary = []
    for lf in f:
    # print("Logical File Attributes:")
        summary.append(f'fileheader: {lf.fileheader.attic["ID"].value[0].strip()}:\n')

    # print(lf.fileheader)
    # print(get_attributes(lf.fileheader))
    # print(lf.fileheader.attic['ID'].value)
        for attr in meta_attr_list:
            attr_value = getattr(lf, attr)
            if len(attr_value) == 0: continue
            summary.append(f'\t{attr}: \n')
            for sub_attr in attr_value:
                subsub_attrs = sub_attr.attic.keys()
                summary.append(f'\t\t{sub_attr.name}: \n')
                for subsub_attr in subsub_attrs:
                # summary.append(f'\t\t\t{subsub_attr.lower()}: \n')
                    value = [x.id if isinstance(x, dlisio.core.obname) else x for x in sub_attr.attic[subsub_attr].value]
                    if len(value)==0: continue
                    if len(value)==1:
                        value = value[0]
                    unit = sub_attr.attic[subsub_attr].units
                    value_str = str(value)
                    if value_str == '': continue
                    value_str = value_str.replace('\r\n', ' ').replace('\n', ' ')
                    if unit != '':
                        summary.append(f'\t\t\t{subsub_attr.lower()}({unit}): {value_str}\n')   
                    else:
                        summary.append(f'\t\t\t{subsub_attr.lower()}: {value_str}\n')

    summary = ''.join(summary)
    return summary

summary = get_meta(f)

with open('summary.txt', 'w') as f:
    f.write(summary)