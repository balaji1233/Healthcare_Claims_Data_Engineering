# Healthcare_Claims_Data_Engineering

One of the major challenges many new data engineers and analysts face when trying to build data projects is finding data sets. In particular, many data sets aren't really the data sets don't tie to specific domains.

That's why I have set-up the data set below. The core data set is the Center For Medicare and Medicaid Services Synthetic data set. That is to say, in their own words, realistic-but-not-real data.

The CMS created these synthetic datasets to allow interested parties to gain familiarity with using Medicare claims data while protecting beneficiary privacy. The Synthetic Medicare Claims data were designed to map to CMS’ Research Identifiable File (RIF) format, meaning that even though they are not tied to any real patient data, they mimic the real claims data that CMS makes available to researchers through the CMS Chronic Conditions Warehouse (CCW).

So this data set will give you all the joys and pains of working with real data.

It has codes and IDs that require translating, it has missing dimesions that I have found such as provider and location data.

It also provides plenty of unique possibilites of projects.

<img width="594" alt="Screen Shot 2024-11-20 at 1 38 34 PM" src="https://github.com/user-attachments/assets/213024d5-5b12-4471-ba7d-656df5d89b41">


## Data Sets

As a data engineer we often need to spend time piecing together data sets that might not all come from one source. Well we are in luck.

There are two different synthetic CMS data sets, one from 2008-2010 and the other from 2015-2023. The first is decently large(in the millions) has multiple files but is older and in turn requires usage of ICD where as the second is considerably smaller.

But two different schema formats, needing to look for other data sets across the internet, guess what you've got yourself a data engineering project that will let you know what it feels like to be a data engineer.

Here is how the data sets are broken down.

- Claims but for CMS they might call this an Encounter (Inpatient, Outpatient, etc)
- Beneficiary - I reference this as patients as it's what I called it when working in claims 
- Provider
- Prescriptions
- NDC - Drug descriptions
- Location broken down by county
- 
<img width="932" alt="Screen Shot 2024-11-20 at 2 06 41 PM" src="https://github.com/user-attachments/assets/df1023d8-8aab-4462-9090-a35a0f4b63fb">

<img width="598" alt="Screen Shot 2024-11-20 at 1 45 49 PM" src="https://github.com/user-attachments/assets/84349c39-ec2e-4812-bc8f-546346b54d02">

## System Design

The overall goal of the system that is being built is that it can easily accomodate new companies data sets. So instead of having to build a new pipeline every time, you'd simply create a new transform script that standardizing the new data to fit the expected output. From their any data product would simply ingest the new data without any issues.

<img width="1192" alt="Screen Shot 2024-12-06 at 7 04 03 PM" src="https://github.com/user-attachments/assets/da196973-17a6-4d1e-ac7b-7c62e029e4cf">
## Important Claims Concepts

It's tempting to dive straight into the data, but its important to understand what the data represents. Otherwise, you're not going to understand why there are multiple ICD codes, and what they represent. You might not understand what inpatient vs outpatient mean and why they are different.

So let's dive into some of the basics around claims data.

---

### **1. ICD Codes (International Classification of Diseases)**

**Purpose**:  
ICD codes are standardized codes used globally to classify and code diseases, symptoms, and procedures. They are critical for documenting diagnoses and conditions. But, what might get confusing is there are both procedure and diagnosis codes.

- **ICD Diagnosis Codes**: 
  - Represent the medical reason for a patient's visit or condition (e.g., diabetes, hypertension).
  - Format: **ICD-10-CM** (e.g., E11.9 for Type 2 Diabetes Mellitus without complications).

- **ICD Procedure Codes**:  
  - Represent procedures performed during inpatient hospital stays and is used for reimbursement, quality reporting, and identifying inpatient care trends.
  - Format: **ICD-10-PCS** (e.g., 0U5B7ZZ for an open hysterectomy).
---

### **2. CPT Codes (Current Procedural Terminology)**

**Purpose**:  
CPT codes describe the specific medical, surgical, and diagnostic services provided by healthcare professionals.

- **Format**: Five-digit numeric codes (e.g., 99213 for a standard outpatient office visit). Some codes also include a modifier for additional specificity.
- **Categories**:
  - **Category I**: Common procedures and services.
  - **Category II**: Performance measurement (optional reporting codes).
  - **Category III**: Emerging technologies and experimental procedures.

---

### **3. HCPCS Codes (Healthcare Common Procedure Coding System)**

**Purpose**:  
HCPCS codes expand on CPT codes to include non-physician services like durable medical equipment (DME), transportation, or drugs.

- **Level I**: Equivalent to CPT codes.
- **Level II**: Covers services and equipment not included in CPT (e.g., E0601 for a CPAP machine).

---

### **4. DRG Codes (Diagnosis-Related Groups)**

**Purpose**:  
DRG codes classify inpatient stays into groups based on diagnoses and procedures. These are used primarily for hospital reimbursement.

- Example: DRG 470 for a major joint replacement or reattachment procedure.

---

### **5. Revenue Codes**

**Purpose**:  
Revenue codes indicate the department or type of service provided (e.g., emergency room, pharmacy). They are essential for understanding claims at the departmental level.

- Example: Revenue code 450 for emergency room services.

---

### **6. NDC (National Drug Codes)**

**Purpose**:  
NDC codes are unique identifiers for drugs and are used in claims involving prescriptions or administered medications.

- Format: 10-11 digit numeric code (e.g., 0781-1506-10 for a specific vial of insulin).


---

### **Practical Use Cases for Analysts**

1. **Cost Analysis**: Identify the highest-cost services and procedures using CPT or HCPCS codes.
2. **Population Health**: Segment populations by diagnosis (ICD codes) to identify trends or disparities in care.
3. **Utilization Analysis**: Determine service utilization rates by department (revenue codes) or service type.
4. **Performance Metrics**: Evaluate healthcare provider performance based on DRG benchmarks or CPT-related outcomes.
5. **Fraud Detection**: Identify anomalies in claims data, such as duplicate billing or mismatched codes.

