# stl-to-amf

Tool to convert, merge and modify stl files through command line. This tool
takes one ore more stls as input, and merge them in one amf. If you add a
configuration file, you can apply a Slicing configuration to the stls. If
specified in the arguments, different configurations can be applied to
different files.

Examples:
```console
$ python stl_to_amf.py file1.stl file2.stl --output_path 'out.amf'

$ python stl_to_amf.py -custom_config --config_path config.yaml file1.stl profile_1 file2.stl profile_2
```
