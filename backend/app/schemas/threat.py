from datetime import datetime
from typing import Optional
from pydantic import BaseModel
class ThreatResponse(BaseModel):
 id:str; project_id:str; scan_id:str; asset_id:Optional[str]=None; vulnerability_id:Optional[str]=None; hostname:Optional[str]=None; ip:Optional[str]=None; url:Optional[str]=None; cve:Optional[str]=None; source:str; cvss:Optional[float]=None; severity:Optional[str]=None; description:Optional[str]=None; published:Optional[datetime]=None; last_modified:Optional[datetime]=None; cwe:Optional[str]=None; references:list=[]; attack_vector:Optional[str]=None; attack_complexity:Optional[str]=None; kev:bool=False; kev_vendor:Optional[str]=None; kev_product:Optional[str]=None; kev_due_date:Optional[datetime]=None; shodan:dict={}; virustotal:dict={}; created_at:datetime; updated_at:datetime; project_name:Optional[str]=None; scan_name:Optional[str]=None
class ThreatListResponse(BaseModel): records:list[ThreatResponse]; total:int; page:int; per_page:int
class ThreatStatsResponse(BaseModel): total_cves:int=0; known_exploited:int=0; average_cvss:Optional[float]=None; critical_cves:int=0; assets_enriched:int=0; last_sync:Optional[datetime]=None; cvss_distribution:list[dict]=[]; severity_distribution:list[dict]=[]; top_vendors:list[dict]=[]; top_products:list[dict]=[]; threat_sources:list[dict]=[]
