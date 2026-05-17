# Operations Guide — <PROGRAM>

**Author:** iA by programmers.io  
**Date:** <YYYY-MM-DD>  
**Library:** <LIBRARY> | **Source:** <SRCPF>  
**Audience:** Operations / Support Team

---

## 1. Program Summary

<Brief description of what this program does and when it runs>

**Operational Classification:**
- **Type:** <Interactive/Batch/Scheduled/On-Demand>
- **Frequency:** <Real-time/Hourly/Daily/Weekly/Monthly/As-Needed>
- **Priority:** <Critical/High/Medium/Low>
- **Support Level:** <24x7/Business Hours/Best Effort>

---

## 2. Runtime Information

### Execution Context

| Attribute | Value |
|-----------|-------|
| Job Type | <Interactive/Batch> |
| Subsystem | <SUBSYSTEM> |
| Job Queue | <JOBQ> (if batch) |
| Typical Runtime | <Duration> |
| Resource Usage | <Low/Medium/High> |

### Scheduling

- **Trigger:** <User-initiated/Scheduled/Event-driven>
- **Schedule:** <Cron expression or description>
- **Dependencies:** <Programs that must run first>

---

## 3. Files and Data

### Files Accessed

| File | Library | Access | Purpose | Backup Required |
|------|---------|--------|---------|-----------------|
| <FILE> | <LIB> | Read/Write/Update | <Purpose> | Yes/No |

### Data Areas Used

| Data Area | Library | Purpose | Critical |
|-----------|---------|---------|----------|
| <DTAARA> | <LIB> | <Purpose> | Yes/No |

### File Locks

- ⚠️ **<FILE>** — Exclusive lock during <operation>
- ⚠️ **<FILE>** — Shared lock for read

---

## 4. Dependencies

### Programs Called

| Program | Purpose | Failure Impact |
|---------|---------|----------------|
| <PGM> | <Purpose> | <Impact if fails> |

### Service Programs Required

| Service Program | Purpose | Version Required |
|-----------------|---------|------------------|
| <SRVPGM> | <Purpose> | <Version> |

### External Systems

- **<System Name>** — <Integration point>
- **<System Name>** — <Integration point>

---

## 5. Error Handling

### Common Errors

| Error Code | Message | Cause | Resolution |
|------------|---------|-------|------------|
| <CODE> | <Message> | <Cause> | <How to fix> |
| <CODE> | <Message> | <Cause> | <How to fix> |

### Error Indicators

| Indicator | Meaning | Action Required |
|-----------|---------|-----------------|
| *IN99 | <Meaning> | <Action> |
| *IN50 | <Meaning> | <Action> |

### Failure Recovery

1. **If program fails:**
   - Check: <What to check>
   - Action: <What to do>
   - Restart: <How to restart>

2. **If data corruption:**
   - Check: <What to check>
   - Action: <What to do>
   - Restore: <How to restore>

---

## 6. Monitoring

### Key Metrics to Monitor

| Metric | Normal Range | Alert Threshold | Action |
|--------|--------------|-----------------|--------|
| Runtime | <X-Y minutes> | ><Z minutes> | <Action> |
| Records Processed | <X-Y> | <<X or >>Y> | <Action> |
| Error Count | 0 | >0 | <Action> |
| CPU Usage | <X%> | ><Y%> | <Action> |

### Log Files

- **Job Log:** <Location>
- **Application Log:** <Location>
- **Error Log:** <Location>

### Health Checks

- ✓ Check 1: <What to verify>
- ✓ Check 2: <What to verify>
- ✓ Check 3: <What to verify>

---

## 7. Maintenance

### Regular Maintenance Tasks

| Task | Frequency | Procedure |
|------|-----------|-----------|
| <Task> | <Daily/Weekly/Monthly> | <Steps> |

### Backup Requirements

- **Before Changes:** <What to backup>
- **Frequency:** <How often>
- **Retention:** <How long>

### Performance Tuning

- **Bottlenecks:** <Known issues>
- **Optimization:** <Tuning recommendations>

---

## 8. Troubleshooting Guide

### Troubleshooting Decision Tree *(mandatory)*

Render one ASCII decision tree mapping common symptoms to diagnostic steps and resolutions. Use a fenced ```` ```text ```` block and box-drawing characters (`├──`, `└──`, `│`). Example shape:

```text
Symptom
├── Job ends abnormally with MCH error
│   ├── MCH3601 (pointer not set) -> check work-field initialization in INITPROC
│   └── MCH1202 (decimal data) -> dump file, verify numeric field contents
├── Job runs but produces no output
│   ├── Empty input file -> check upstream feed job log
│   └── All records filtered -> verify selection criteria in SELRPT
└── Job hangs / no progress
    ├── File lock from another job -> WRKOBJLCK, identify holder, escalate
    └── Database deadlock -> review recent commitment-control changes
```

### Problem: Program Runs Slowly

**Symptoms:**
- <Symptom 1>
- <Symptom 2>

**Possible Causes:**
1. <Cause 1> → Check: <What to check>
2. <Cause 2> → Check: <What to check>

**Resolution:**
- <Step 1>
- <Step 2>

---

### Problem: Program Fails to Start

**Symptoms:**
- <Symptom 1>
- <Symptom 2>

**Possible Causes:**
1. <Cause 1> → Check: <What to check>
2. <Cause 2> → Check: <What to check>

**Resolution:**
- <Step 1>
- <Step 2>

---

### Problem: Data Errors

**Symptoms:**
- <Symptom 1>
- <Symptom 2>

**Possible Causes:**
1. <Cause 1> → Check: <What to check>
2. <Cause 2> → Check: <What to check>

**Resolution:**
- <Step 1>
- <Step 2>

---

## 9. Contacts

### Escalation Flow Tree *(mandatory)*

Render one ASCII flow tree showing who to contact for which class of issue, in order. Use a fenced ```` ```text ```` block and box-drawing characters (`├──`, `└──`, `│`). Example shape:

```text
Incident
├── Severity 1 (production down)
│   ├── Page on-call IBM i admin immediately
│   └── If unresolved in 30 min -> page application owner
├── Severity 2 (degraded function)
│   └── Open ticket -> assign to application team
└── Severity 3 (data anomaly, non-blocking)
    └── Email application team -> next business day
```

### Support Escalation

| Level | Contact | When to Escalate |
|-------|---------|------------------|
| L1 | <Team/Person> | <Criteria> |
| L2 | <Team/Person> | <Criteria> |
| L3 | <Team/Person> | <Criteria> |

### Subject Matter Experts

- **Developer:** <Name/Team>
- **Business Owner:** <Name/Team>
- **DBA:** <Name/Team>

---

## 10. Change History

| Date | Version | Change | Changed By |
|------|---------|--------|------------|
| <YYYY-MM-DD> | <Version> | <Description> | <Name> |

### Last Compiled

- **Date:** <YYYY-MM-DD>
- **Time:** <HH:MM:SS>
- **By:** <User>

### Last Modified

- **Date:** <YYYY-MM-DD>
- **Source Changed:** <Yes/No>
- **Recompile Required:** <Yes/No>

---

## Operational Readiness

| Aspect | Status | Notes |
|--------|--------|-------|
| Documentation | <✅/⚠️> | <Notes> |
| Monitoring | <✅/⚠️> | <Notes> |
| Error Handling | <✅/⚠️> | <Notes> |
| Backup Procedures | <✅/⚠️> | <Notes> |
| Support Contacts | <✅/⚠️> | <Notes> |

**Overall Readiness:** <Ready/Needs Attention/Not Ready>

---

*Analysis powered by iA from [programmers.io](https://programmers.io/ia/)*
