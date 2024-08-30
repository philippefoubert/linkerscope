import re
import yaml

from section import Section


class DCCLinkerMapParser:
    """
    Parse a DCC (DiabData) linker map file and convert it to a yaml file for further processing
    """
    def __init__(self, input_filename, output_filename):
        self.sections = []
        self.subsections = []
        self.input_filename = input_filename
        self.output_filename = output_filename

    def parse(self):
        with open(self.input_filename, 'r', encoding='utf8') as file:

            file_iterator = iter(file)
            prev_line = next(file_iterator)
            for line in file_iterator:
                self.process_areas(prev_line)
                multiple_line = prev_line + line
                self.process_sections(multiple_line)
                prev_line = line

        my_dict = {'map': []}
        for section in self.sections:
            my_dict['map'].append({
                'type': 'area',
                'address': section.address,
                'size': section.size,
                'id': section.id,
                'flags': section.flags
            })

        for subsection in self.subsections:
            my_dict['map'].append({
                'type': 'section',
                'parent': subsection.parent,
                'address': subsection.address,
                'size': subsection.size,
                'id': subsection.id,
                'flags': subsection.flags
            })

        with open(self.output_filename, 'w', encoding='utf8') as file:
            yaml_string = yaml.dump(my_dict)
            file.write(yaml_string)

    def process_areas(self, line):
        # In "linkerscope\examples\sample_map.map", parses:
        #   .rtc.data       0x0000000050000000       0x10
        #                   0x0000000050000000                _rtc_data_start = ABSOLUTE (.)
        #                   0x0000000050000000                _coredump_rtc_start = ABSOLUTE (.)
        # to get:
        #   - address: 1342177280
        #     flags: *id001
        #     id: .data
        #     size: 16
        #     type: area
        pattern = r'([.][a-z]{1,})[ ]{1,}(0x[a-fA-F0-9]{1,})[ ]{1,}(0x[a-fA-F0-9]{1,})\n'

        p = re.compile(pattern)
        result = p.search(line)

        if result is not None:
            self.sections.append(Section(parent=None,
                                         id=result.group(1),
                                         address=int(result.group(2), 0),
                                         size=int(result.group(3), 0),
                                         _type='area'
                                         )
                                 )

    def process_sections(self, line):
        #GNU: # In "linkerscope\examples\sample_map.map", parses:
        #GNU: #   " .literal.get_default_pthread_core"
        #GNU: #   "                0x0000000000000000        0x4 esp-idf/pthread/libpthread.a(pthread.c.obj)"
        #GNU: # to get:
        #GNU: #   - address: 0
        #GNU: #     flags: *id001
        #GNU: #     id: get_default_pthread_core
        #GNU: #     parent: .literal
        #GNU: #     size: 4
        #GNU: #     type: section
        #GNU: pattern = r'\s(.[^.]+).([^. \n]+)[\n\r]\s+(0x[0-9a-fA-F]{16})\s+' \
        #GNU:           r'(0x[0-9a-fA-F]+)\s+[^\n]+[\n\r]{1}'

        #DCC: #		Link Editor Memory Map
        #DCC: #output          input           virtual
        #DCC: #section         section         address         size     file
        #DCC: #   ".rodata_module_APSAgent_C001    0000000002801000        0000000000008732 "
        #DCC: #   "                .rodata         0000000002800000        0000000000000228 CMakeFiles/appli1_p1.dir/temp/backend/binary_bridge.o"
        #DCC: #   "                    ast_uid_psy 0000000002800000        0000000000000080 "
        #DCC: #   "       ast_W_FHC_REGUL_init_psy 0000000002800080        0000000000000008 "
        #DCC: #   "ast_W_FHC_REGUL_errorid_software_error_psy 0000000002800088        0000000000000004 "
        pattern = r'^(\.[^. \n]+)\s+([0-9a-fA-F]*)\s+' \
                  r'([0-9a-fA-F]*)\s+'

        p = re.compile(pattern)
        result = p.search(line)

        if result is not None:
            val_flags = ''
            # val_size  = int(result.group(3), 16)
            # if (val_size > 0xb00000):
            #     val_flags = 'break'
            self.subsections.append(Section(parent=None,
                                            id=result.group(1),
                                            address=int(result.group(2), 16),
                                            size=int(result.group(3), 16),
                                            flags=val_flags,
                                            _type='section'
                                            )
                                    )
