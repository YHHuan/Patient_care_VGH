"""URL constants for VGHTPE EMR system, derived from senior's VGH_function.py."""

BASE_EIP = "https://eip.vghtpe.gov.tw"
BASE_EMR = "https://web9.vghtpe.gov.tw/emr/qemr/qemr.cfm"
BASE_NIS = "https://web9.vghtpe.gov.tw/NIS"
ROOT_URL = "https://web9.vghtpe.gov.tw"

# Auth
LOGIN_PAGE = f"{BASE_EIP}/login.php"
LOGIN_ACTION = f"{BASE_EIP}/login_action.php"

# Patient list
PATIENT_SEARCH = f"{BASE_EMR}?action=findPatient"
MY_PATIENTS = f"{BASE_EMR}?action=findPatient&srnId=DRWEBAPP&"


def patient_search_url(*, ward: str = "0", hist_no: str = "", doc_id: str = "") -> str:
    return (
        f"{BASE_EMR}?action=findPatient&wd={ward}&histno={hist_no}"
        f"&pidno=&namec=&drid={doc_id}&er=0&bilqrta=0&bilqrtdt=&bildurdt=0&other=0&nametype="
    )


# Per-patient endpoints (all take histno= or caseno=)
def emr_url(hist_no: str) -> str:
    return f"{BASE_EMR}?action=findEmr&histno={hist_no}"


def admin_id_url(hist_no: str) -> str:
    """PBV page — parse first <option> value to get caseno (adminID)."""
    return f"{BASE_EMR}?action=findPbv&histno={hist_no}"


def tpr_url(case_no: str) -> str:
    return f"{BASE_EMR}?action=findTpr&caseno={case_no}"


def tpr_img_url(case_no: str) -> str:
    return f"{BASE_EMR}?action=findTpr&caseno={case_no}&pbvtype=tpr"


def bw_bl_url(hist_no: str, case_no: str = "all") -> str:
    return f"{BASE_EMR}?action=findVts&histno={hist_no}&caseno={case_no}&pbvtype=HWS"


def lab_value_url(hist_no: str, resd_type: str = "DCHEM", months: str = "24") -> str:
    return f"{BASE_EMR}?action=findResd&resdtype={resd_type}&histno={hist_no}&resdtmonth={months}"


def admission_url(hist_no: str) -> str:
    return f"{BASE_EMR}?action=findAdm&histno={hist_no}"


def drug_url(hist_no: str) -> str:
    return f"{BASE_EMR}?action=findUd&histno={hist_no}"


def res_report_url(hist_no: str, resd_type: str = "DCHEM", months: str = "00") -> str:
    return f"{BASE_EMR}?action=findResd&resdtype={resd_type}&histno={hist_no}&resdtmonth={months}"


def recent_report_url(hist_no: str) -> str:
    return f"{BASE_EMR}?action=findRes&tdept=ALL&histno={hist_no}"


def progress_note_url(hist_no: str, case_no: str) -> str:
    return f"{BASE_EMR}?action=findPrg&histno={hist_no}&caseno={case_no}"


def nis_io_url(hist_no: str, case_no: str) -> str:
    return f"{BASE_EMR}?action=goNIS&hisid={hist_no}&caseno={case_no}"


def nis_io_detail_url(date_str: str) -> str:
    """date_str in YYYYMMDD format."""
    return f"{BASE_NIS}/report/IORpt/details.do?gaugeDate1={date_str}"


def op_url(hist_no: str) -> str:
    return f"{BASE_EMR}?action=findOpb&histno={hist_no}"


def admin_intro_url(hist_no: str) -> str:
    return f"{BASE_EMR}?action=findPba&histno={hist_no}"


# Lab report type mapping (user-friendly → internal code)
LAB_REPORT_TYPES = {
    "SMAC": "DCHEM",
    "CBC": "DCBC",
    "Urine": "DURIN",
    "Cancer": "DNM1",
}
