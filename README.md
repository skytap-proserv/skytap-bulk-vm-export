# skytap-bulk-vm-export

Export VMs frm Skytap in bulk.

Version 1.1

## Requirements

- [Skytap REST API wrapper](http://skytap.readthedocs.io/en/latest/) v1.4.0 or better

## Uaage

To use this exporter, simply call it form the command line with the -t switch and a template id.

`bulk-export.py -t 12345`


## Notes

- Skytap imposes a limit on the number of import/export jobs that may be run concurrently.  `bulk-export.py` will spawn an additional thread per currently exporting VM, up to the number of available export slots, plus two.  If your import/export limit is set to Skytap's default of 5, bulk-export will never consume more than 7 threads.  If however you have requested additional import/export slots, this will increase the number of potential threads that `bulk-export.py` may use, and increase the amount of memory the export process consumes on your local machine.

- Added the ability to export several templates with one command `bulk-export -t 1234 2345 3456`
