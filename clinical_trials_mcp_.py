from mcp.server.fastmcp import FastMCP
from parsers_ import (
    format_search_trials_summary,
    format_ct_gov_study_batch,
    format_ctgov_trial_details,
    extract_cro_data,
)
from models_ import model_call
from typing import Optional
import requests
import asyncio

mcp = FastMCP("clinical-trials-mcp", working_dir=".")


@mcp.tool()
def fetch_trial(
    eu_ct_id: str = None,
    trial_ct_id: str = None,
):
    """
    Fetch full trial information from euclinicaltrials.eu or ClinicalTrials.gov based on trial ID. Send in either EU trial ID or NCT ID, not both.

    Args:
        eu_ct_id: Specific EU trial identifier number (ctNumber) to look up
        trial_ct_id: Specific NCT ID to look up
    """
    if eu_ct_id and trial_ct_id:
        return f"Both EU trial ID ({eu_ct_id}) and ClinicalTrials.gov ID ({trial_ct_id}) were provided. Only one ID can be processed at a time. Processing the ClinicalTrials.gov ID first. Please run this tool again with only the EU trial ID to fetch that data separately."
    if trial_ct_id:
        if not trial_ct_id.startswith("NCT"):
            return f"Invalid NCT ID format: {trial_ct_id}. IDs should start with 'NCT' followed by 8 digits."
        try:
            url = f"https://clinicaltrials.gov/api/v2/studies/{trial_ct_id}"
            params = {"format": "json", "markupFormat": "markdown"}
            response = requests.get(url, params=params)
            response.raise_for_status()
            study_data = response.json()
            formatted_result = format_ctgov_trial_details(study_data)
            return formatted_result
        except Exception as e:
            return f"Error fetching study with ID {trial_ct_id}: {str(e)}"
    if eu_ct_id:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "origin": "https://euclinicaltrials.eu",
        }
        try:
            api_url = f"https://euclinicaltrials.eu/ctis-public-api/retrieve/{eu_ct_id}"
            response = requests.get(
                api_url,
                cookies={"accepted_cookie": "true"},
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            raw_data = response.json()
            extracted_data = extract_cro_data(raw_data)
            full_summary = extracted_data["summary"]
            return full_summary
        except requests.RequestException as err:
            return f"Error querying EU Clinical Trials: {err}"
    return (
        "Please provide either an EU clinical trial ID or a ClinicalTrials.gov NCT ID."
    )


@mcp.tool()
async def search_batch_trials(
    user_request: str,
    search_terms: str,
    condition: Optional[str] = None,
    location: Optional[str] = None,
    sponsor: Optional[str] = None,
    status: Optional[str] = None,
    no_of_trials: int = 10,
):
    """
    Search for clinical trials based on user request and search terms. Fetch data from both EU Clinical Trials and ClinicalTrials.gov.

    Args:
        user_request: User's specific request or question regarding clinical trials.
        search_terms: Keywords or phrases to search for in clinical trials.
        condition: Specific condition or disease to filter trials.
        location: Trial's location (city, state, country).
        sponsor: Sponsor of the trial.
        status: Status of the trial - 8 for ended, 5 for ongoing recruitment ended, 1 for authorised, 4 for ongoing recruiting.
        no_of_trials: Number of trials to fetch from each source (default is 10).
    """
    query = search_terms or user_request
    cond = condition or ""
    locn = location or ""
    spons = sponsor or ""
    status = int(status) if status else 8
    if not query or not user_request:
        return f"error: Missing required parameters. Please provide a search term and user request."
    all_eu_trials = []
    all_eu_llm_responses = []
    all_ct_gov_llm_responses = []
    processed_eu_trial_count = 0
    processed_ct_count = 0
    try:
        search_criteria = {
            "containAll": search_terms,
            "status": [
                status,
            ],
        }
        if cond:
            search_criteria["medicalCondition"] = cond
        if spons:
            search_criteria["sponsor"] = spons
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "origin": "https://euclinicaltrials.eu",
        }
        current_page = 1
        has_next = True
        eu_trial_ids = []
        eu_page_count = 0
        while has_next and len(eu_trial_ids) < no_of_trials:
            payload = {
                "pagination": {"page": current_page, "size": 5},
                "sort": {"property": "decisionDate", "direction": "DESC"},
                "searchCriteria": search_criteria,
            }
            response = requests.post(
                "https://euclinicaltrials.eu/ctis-public-api/search",
                cookies={"accepted_cookie": "true"},
                headers=headers,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            trials_in_batch = data.get("data", [])
            for trial in trials_in_batch:
                if "ctNumber" in trial:
                    eu_trial_ids.append(trial["ctNumber"])
                    if len(eu_trial_ids) >= no_of_trials:
                        break
            eu_page_count += 1
            has_next = data.get("pagination", {}).get("nextPage", False)
            if not has_next or len(eu_trial_ids) >= no_of_trials:
                break
            current_page += 1
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "format": "json",
            "markupFormat": "markdown",
            "query.term": query.replace(" ", "+"),
            "filter.overallStatus": "COMPLETED",
            "pageSize": 5,
        }
        if cond:
            params["query.cond"] = cond
        if locn:
            params["query.locn"] = locn
        if spons:
            params["query.spons"] = spons
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        total_count = min(data.get("totalCount", no_of_trials), no_of_trials)
        ct_gov_page_count = (total_count + 4) // 5

        async def process_eu_page(page_num):
            payload = {
                "pagination": {"page": page_num, "size": 5},
                "sort": {"property": "decisionDate", "direction": "DESC"},
                "searchCriteria": search_criteria,
            }
            response = await asyncio.to_thread(
                requests.post,
                "https://euclinicaltrials.eu/ctis-public-api/search",
                cookies={"accepted_cookie": "true"},
                headers=headers,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            summary = format_search_trials_summary(data)
            return summary, data.get("data", [])

        eu_tasks = []
        for page in range(1, eu_page_count + 1):
            eu_tasks.append(process_eu_page(page))
        eu_results = await asyncio.gather(*eu_tasks)
        eu_summaries = []
        for summary, trials in eu_results:
            all_eu_trials.append(summary)
            processed_eu_trial_count += len(trials)
            if summary:
                eu_summaries.append(summary)

        async def analyze_eu_trial(summary, idx):
            prompt = f"""
            The user is looking for information about: "{user_request}"
            
            Below are some EU clinical trial summaries. Identify which (if any) of these trials 
            are relevant to the user's request. Prefer complete or ongoing trials. Prefer trials from pharmaceutical companies or trials that have results.
            For each relevant trial, provide:
            1. The Trial ID (ctNumber)
            2. A brief explanation of why it's relevant
            
            If none are relevant, state that clearly.
            Be succint.
            
            {summary}
            """
            llm_response = await model_call(
                messages=prompt, model="claude-3-5-haiku-20241022"
            )
            return idx, llm_response.content

        eu_llm_tasks = []
        for i, summary in enumerate(eu_summaries):
            if user_request:
                eu_llm_tasks.append(analyze_eu_trial(summary, i))
        if eu_llm_tasks:
            eu_llm_results = await asyncio.gather(*eu_llm_tasks)
            eu_llm_results.sort(key=lambda x: x[0])
            for _, response_text in eu_llm_results:
                all_eu_llm_responses.append(response_text)

        async def process_ct_gov_page(page_token=""):
            params = {
                "format": "json",
                "markupFormat": "markdown",
                "query.term": query.replace(" ", "+"),
                "filter.overallStatus": "COMPLETED",
                "pageSize": 5,
            }
            if page_token:
                params["pageToken"] = page_token
            response = await asyncio.to_thread(requests.get, url, params=params)
            response.raise_for_status()
            data = response.json()
            studies = data.get("studies", [])
            next_token = data.get("nextPageToken", "")
            batch_formatted = format_ct_gov_study_batch(studies)
            return batch_formatted, studies, next_token

        first_batch, studies, next_token = await process_ct_gov_page()
        processed_ct_count += len(studies)
        ct_gov_batches = []
        if first_batch:
            ct_gov_batches.append(first_batch)
        batch_tasks = []
        tokens = []
        while next_token and processed_ct_count < no_of_trials:
            tokens.append(next_token)
            if len(tokens) >= ct_gov_page_count - 1:
                break
        for token in tokens:
            batch_tasks.append(process_ct_gov_page(token))
        if batch_tasks:
            ct_results = await asyncio.gather(*batch_tasks)
            for batch_formatted, studies, _ in ct_results:
                if batch_formatted:
                    ct_gov_batches.append(batch_formatted)
                processed_ct_count += len(studies)

        async def analyze_ct_gov_trial(batch_formatted, idx):
            prompt = f"""
            The user is looking for information about: "{user_request}"

            Below are some clinical trial summaries from ClinicalTrials.gov. Identify which (if any) of these trials
            are relevant to the user's request. Prefer complete or ongoing trials. Prefer trials from pharmaceutical companies or trials that have results.
            For each relevant trial, provide:
            1. The NCT ID
            2. A brief explanation of why it's relevant

            If none are relevant, state that clearly.
            Be succint.

            {batch_formatted}
            """
            llm_response = await model_call(
                messages=prompt, model="claude-3-5-haiku-20241022"
            )
            return idx, llm_response.content

        ct_gov_llm_tasks = []
        for i, batch_formatted in enumerate(ct_gov_batches):
            if user_request:
                ct_gov_llm_tasks.append(analyze_ct_gov_trial(batch_formatted, i))
        if ct_gov_llm_tasks:
            ct_gov_llm_results = await asyncio.gather(*ct_gov_llm_tasks)
            ct_gov_llm_results.sort(key=lambda x: x[0])
            for _, response_text in ct_gov_llm_results:
                all_ct_gov_llm_responses.append(response_text)
    except Exception as e:
        error_message = f"Error searching clinical trials: {str(e)}"
        return f"error: {error_message}"
    result = f"# Clinical Trials Search Results for: {query}\n\n"
    if all_eu_trials:
        result += "## EU Clinical Trials Results\n\n"
        if all_eu_llm_responses:
            result += "### EU Trials Analysis\n\n"
            for i, response in enumerate(all_eu_llm_responses, 1):
                result += f"#### Batch {i} Analysis\n{response}\n\n"
        else:
            result += "No EU trials were analyzed for relevance.\n\n"
    if all_ct_gov_llm_responses:
        result += "## ClinicalTrials.gov Results\n\n"
        result += f"Found further clinical trials matching: {query}\n\n"
        result += "### ClinicalTrials.gov Analysis\n\n"
        for i, response in enumerate(all_ct_gov_llm_responses, 1):
            result += f"#### Batch {i} Analysis\n{response}\n\n"
    else:
        result += "## ClinicalTrials.gov Results\n\n"
        result += "No relevant trials were found on ClinicalTrials.gov or analysis failed.\n\n"
    result += "## Summary of Most Relevant Trials\n\n"
    result += "Based on the analysis above, these trials appear most relevant to your query. Consider using the fetch_trials tool to get complete details on specific trials of interest.\n\n"
    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
