---
id: 2026-11-10-robot-rig-whea-records-at-boot-and-driver-install
title: Robot rig WHEA records at boot and driver install, read 2026-11-10
date: 2026-11-10
kind: rig-fact
relevance: reference
fields: [studio-rig, gpu-computing]
tags: [rtx-5090, whea, pci-express, event-log, firmware]
---

## Summary

The Robot rig's Windows System log holds 915 WHEA-Logger records, as read on 2026-11-10; the log goes back to
5 October 2026. 911 are event id 17 (a PCI Express error report) and every one of them carries the same status
values and follows either a boot or a display-driver install by seconds. 4 are event id 1, a firmware record handed
over at four boots in late October, and what they record is not known. No WHEA record falls inside any of the
local training windows checked. This entry says what these records are and nothing wider about the card or the
link. It adds to [[2026-10-07-robot-rig-cuda-stack]].

## Key points

**Extent.** System log as read 2026-11-10, oldest record 2026-10-05. WHEA-Logger: 915 records, the oldest on
2026-10-05 and the newest on 2026-11-09 at 08:04. Event id 17: 911. Event id 1: 4.

**Event id 17 (911 records).**

- The same in every record: UncorrectableErrorStatus 0x100000, CorrectableErrorStatus 0xa000, Status 0x10,
  ErrorSource 4.
- The header log's first word is 0x04000001 in every record (a type-0 configuration read of length 1), register
  offset 0, target bus 02.
- Two reporting devices: 02:00.0 (vendor 0x10de, device 0x2b85, subsystem 8E38103C, revision A1), 484 records;
  and 02:00.1 (vendor 0x10de, device 0x22e8), 427 records.
- The status bits, from the Linux kernel's `include/uapi/linux/pci_regs.h` (fetched 2026-11-10):
  - line 784: `PCI_ERR_UNC_UNSUP 0x00100000 /* Unsupported Request */`
  - line 806: `PCI_ERR_COR_ADV_NFAT 0x00002000 /* Advisory Non-Fatal */`
  - line 808: `PCI_ERR_COR_LOG_OVER 0x00008000 /* Header Log Overflow */`
  - 0x2000 + 0x8000 = 0xa000. So each record is an Unsupported Request, reported as an advisory non-fatal error,
    with the header-log-overflow bit set. The PCI Express specification itself was not opened.
- **Timing.** Every id-17 record follows a boot record (Kernel-General id 12) within 22 s, or a display-driver
  install record (UserPnp id 20003 for the 0x2b85 device) within 5 s. 800 follow a boot; 111 follow an install.
  The log holds exactly three such install records, and each is followed by a group of 37.
- **Bursts.** With a gap over 120 s starting a new burst there are 39: 14 of 2 records, one of 17, and 24 of 33 to
  39.
- **One burst read target by target, and its oddity.** The 2026-11-09 08:04 burst (37 records) names 02:00.2
  twice, once per reporter, then 02:00.3 to 02:00.7 and 02:01.0 to 02:1e.0, and never 02:1f.0. The targets of the
  other full bursts were not listed.
- No sleep or resume records are in the log, so no record can be tied to a resume.

**Event id 1 (4 records, level Error).**

- Times: 2026-10-27 15:59:37, 2026-10-29 22:21:55, 2026-10-30 16:52:40 and 16:53:45. Each is 13 to 18 s after a
  boot record, at four consecutive boots. No boot before 2026-10-27 15:59 or after 2026-10-30 16:53 has one.
- The record header is the same in all four: a common platform error record of 9,496 bytes with 6 sections,
  error severity 1, notification type 3d61a466-ab40-409a-a698-f362d464b38f.
- All 6 sections have type 81212a96-09ed-4996-9471-8d729c8e69ed and severity 1.
- By the UEFI Specification 2.10, Appendix N: that notification type is BOOT, that section type is the Firmware
  Error Record Reference, and severity 1 is "fatal" in the record's own scale.
- Every section body starts: record type 2, revision 2, record identifier 0, record GUID
  8f87f311-c998-4d9e-a0c4-6065518c4f6d. coreboot's `cper.h` names that GUID as the crash-log record. That this
  rig's firmware uses the GUID the same way is an inference.
- The payloads were not decoded. Their first 32 bytes match across the four records, except one byte in one section
  of the first record.
- **The unclean-shutdown reading does not fit.** Three of the four follow a complete, requested shutdown. Four other
  boots that followed an unclean restart (Kernel-Power id 41) have no id-1 record.
- No firmware update was found in the log for that window. What the stored record is about, what created it and
  what cleared it: **not known.**

**Training windows.** The newest WHEA record is 2026-11-09 08:04:53. The earliest local training window checked
opened at 08:36:12 that day. No WHEA record of either id falls inside any of the six windows checked (five on
9 to 10 November, and one on 10 November still running at the read). Earlier runs were not compared.

**Not read further.** The display driver logged 51 records of its own (id 153, 2026-10-10 to 2026-11-04). Their
content was not analysed and this entry draws nothing from them.

## What would not fit this signature

The id-17 records above are one signature: these status values, these two reporters, seconds after a boot or a
driver install. Any of the following would be a different thing and would need its own read:

- other bits in UncorrectableErrorStatus or CorrectableErrorStatus;
- a record that follows neither a boot nor a display-driver install;
- a WHEA record inside a training window (the per-window count so far is 0);
- a new id-1 record.

## Studio relevance

Reference. Runs on the rig are logged with a per-window WHEA count, and this entry is the baseline that count is
read against: 0 inside a window is the expected value, and the boot-time records are not counted as run errors.
The entry does not say the card, the slot or the link is healthy in general. Re-read the log after a firmware
update, a driver change that alters the pattern, or any of the four cases above.

## Claims

- [verified] The System log as read 2026-11-10 (back to 2026-10-05) holds 915 WHEA-Logger records: 911 of id 17 and 4 of id 1. (via: R&D's event-log read on the rig, 2026-11-10; the Publisher's independent read, 2026-11-10)
- [verified] All 911 id-17 records carry UncorrectableErrorStatus 0x100000 and CorrectableErrorStatus 0xa000, reported by 02:00.0 (484) or 02:00.1 (427). (via: R&D's event-log read on the rig, 2026-11-10; the Publisher's independent read, 2026-11-10)
- [verified] Every id-17 record follows a boot record within 22 s or a display-driver install record within 5 s; 111 of the 911 follow an install. (via: R&D's event-log read on the rig, 2026-11-10)
- [verified] 0x100000 is Unsupported Request, 0x2000 is Advisory Non-Fatal and 0x8000 is Header Log Overflow. (via: Linux `include/uapi/linux/pci_regs.h` lines 784, 806 and 808, fetched 2026-11-10)
- [verified] The four id-1 records are boot-notification records whose six sections are Firmware Error Record References, by the GUIDs in UEFI 2.10 Appendix N. (via: R&D's decode of the record bytes and a read of the specification page, 2026-11-10)
- [verified] Three of the four id-1 records follow a complete, requested shutdown. (via: R&D's event-log read on the rig, 2026-11-10)
- [verified] No WHEA record falls inside any of the six local training windows checked (2026-11-09 to 2026-11-10). (via: R&D's comparison of record times with its run notes, 2026-11-10; the Publisher's ledger)
- [unverified] The id-17 records are the two functions of the graphics card answering a configuration scan of bus 02 for functions and devices that are not there. The reading came from a Gemini 4 Argon analysis of the records; the status bits and the timing fit it, and nothing in the log contradicts it.
- [unverified] Which component does the scan (a startup service after boot, the driver installer after an install) is not identified.
- [unverified] Why some bursts hold 2 records and others 33 to 39 is not established. The explanation offered, that the header log keeps the first error while later ones only set the overflow bit, has not been checked; the 2026-11-09 08:04 burst (02:00.2 twice, no 02:1f.0) bears on it.
- [unverified] The firmware record behind the four id-1 records is a crash log in coreboot's sense of that GUID. What it records is not known.

## Sources

- [rig] Get-WinEvent on the System log, provider Microsoft-Windows-WHEA-Logger (ids 1 and 17), read 2026-11-10; field values only
- [rig] Get-WinEvent on the System log for Kernel-General id 12, UserPnp id 20003, Kernel-Power ids 41, 42, 107 and 109, User32 id 1074 and EventLog id 6006, read 2026-11-10
- [primary] https://github.com/torvalds/linux/blob/master/include/uapi/linux/pci_regs.h — Linux kernel, PCI Express AER status bit definitions (lines 784, 806, 808 as fetched 2026-11-10)
- [primary] https://uefi.org/specs/UEFI/2.10/Apx_N_Common_Platform_Error_Record.html — UEFI Forum, UEFI Specification 2.10, Appendix N (N.2.1.1, N.2.2, Table N.1, N.2.10)
- [primary] https://github.com/coreboot/coreboot/blob/main/src/include/cper.h — coreboot, `FW_ERR_RECORD_ID_CRASHLOG_GUID` (lines 512 to 514 as fetched 2026-11-10)
- [user] A Gemini 4 Argon analysis of the id-17 records (2026-11-10): the origin of the configuration-scan reading, not a source for any fact above
