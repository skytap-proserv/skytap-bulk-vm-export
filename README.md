# skytap-bulk-vm-export

Export VMs frm Skytap in bulk.

Version 1.0

## Requirements

- [Skytap REST API wrapper](http://skytap.readthedocs.io/en/latest/) v1.4.0 or better

## Uaage

    $ python bulk_export.py -h
    usage: bulk_export.py [-h] [-o OUTPUT_DIR] [-t TEMPLATES [TEMPLATES ...]]
                          [-v VMS [VMS ...]] [-d DOWNLOAD]

    optional arguments:
      -h, --help            show this help message and exit
      -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                            path to output directory.  A directory with the template ID will be created here, and your VMs will be placed inside.
      -t TEMPLATES [TEMPLATES ...], --templates TEMPLATES [TEMPLATES ...]
                            export a list of templates. Takes space delimited
                            template IDs as arguments.
      -v VMS [VMS ...], --vms VMS [VMS ...]
                            export a list of virtual machines. Takes space
                            delimited VM IDs as arguments.
      -d DOWNLOAD, --download DOWNLOAD
                            download a single job. Takes single export job ID as
                            an argument.
    $

Generally, this script will be run using only the `-o` and `-t` options.  That is, a user will generally specify an output directory and one or more template ids.

    -o  --output_dir      Specify an output directory other than the cwd.  A directory with the template ID
                          will be created here, and the VMs will be downloaded into that.  For example if you are downloading template `12345`, and you specify ``"/path/to/downloads"`` as your `output_dir`, your VMs will be in `/path/to/downloads/12345/`.

    -t --templates        Specify a space delimited list of template ids to be exported and downloaded.

    -v --vms              Specify a space delimited list of VM ids to be exported and downloaded.
                          For use when you need to expprt/download a single VM from a template, but not the whole template.  Useful if something should go wrong during the template export process.

    -d --download         Specify a space delimited list of Export Job ids to be downloaded.  For use
                          when you need to download a single Export Job.  Useful if something should go wrong during the download process.



## Notes

- Skytap imposes a limit on the number of import/export jobs that may be run concurrently.  `bulk-export.py` will spawn an additional thread per currently exporting VM, up to the number of available export slots, plus two.  If your import/export limit is set to Skytap's default of 5, bulk-export will never consume more than 7 threads.  If however you have requested additional import/export slots, this will increase the number of potential threads that `bulk-export.py` may use, and increase the amount of memory the export process consumes on your local machine.

## Examples

`bulk-export.py -o /home/USERNAME/vm_downloads -t 12345`  Will download the VMs in template 12345 to the specified output directory.

## Events for which this script will fall over

- Loss of network connectivity, specifically to Skytap's API when a call is made will be fairly catastrophic.  The script will not recover gracefully from this situation.
