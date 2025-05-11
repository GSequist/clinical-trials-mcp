from typing import Dict, Any, List
import json

##############################################################################
# euclinicaltrials parsers


def safe_extract(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    try:
        value = data
        for key in keys:
            if value is None:
                return default
            value = value.get(key, default)
        return value
    except (KeyError, TypeError, AttributeError):
        return default


def format_search_trials_summary(data: Dict[str, Any]) -> str:
    total_records = safe_extract(data, "pagination", "totalRecords", default=0)
    current_page = safe_extract(data, "pagination", "currentPage", default=1)
    total_pages = safe_extract(data, "pagination", "totalPages", default=1)
    has_next = safe_extract(data, "pagination", "nextPage", default=False)

    summary = f"""
Search Results Summary:
Total Records: {total_records}
Current Page: {current_page} of {total_pages}
More Pages Available: {"Yes" if has_next else "No"}

Trial Details:
"""
    trials = safe_extract(data, "data", default=[])
    for trial in trials:
        countries = [
            c.split(":")[0] for c in safe_extract(trial, "trialCountries", default=[])
        ]

        trial_details = f"""
----------------------------------------
Trial ID: {safe_extract(trial, "ctNumber", default="N/A")}
Status: {safe_extract(trial, "ctStatus", default="N/A")}
Title: {safe_extract(trial, "ctTitle", default="N/A")}
Short Title: {safe_extract(trial, "shortTitle", default="N/A")}
Start Date: {safe_extract(trial, "startDateEU", default="N/A")}
Sponsor: {safe_extract(trial, "sponsor", default="N/A")} ({safe_extract(trial, "sponsorType", default="N/A")})
Condition: {safe_extract(trial, "conditions", default="N/A")}
Phase: {safe_extract(trial, "trialPhase", default="N/A")}
Countries: {', '.join(countries)}
Population: {safe_extract(trial, "ageGroup", default="N/A")}, {safe_extract(trial, "gender", default="N/A")}
Enrollment: {safe_extract(trial, "totalNumberEnrolled", default="N/A")} participants
Results Available: {safe_extract(trial, "resultsFirstReceived", default="No")}
Last Updated: {safe_extract(trial, "lastUpdated", default="N/A")}

Primary Endpoint: {safe_extract(trial, "primaryEndPoint", default="N/A")}
Other Endpoints: {safe_extract(trial, "endPoint", default="N/A")}
Products: {safe_extract(trial, "product", default="N/A")}
Therapeutic Areas: {', '.join(safe_extract(trial, "therapeuticAreas", default=[]))}
----------------------------------------
"""
        summary += trial_details

    return summary


def format_detailed_trial_summary(data: Dict[str, Any]) -> str:
    basic = data.get("basic_info", {})
    products = data.get("products", [])
    details = data.get("trial_details", {})
    sponsors = data.get("sponsors", [])
    category = data.get("category_details", {})
    auth_parts = data.get("authorized_parts", [])
    events_docs = data.get("events_and_documents", {})
    summary_parts = []
    if basic:
        summary_parts.extend(
            [
                "=== BASIC TRIAL INFORMATION ===",
                f"Clinical Trial ID: {basic.get('trial_id', 'Not specified')}",
                f"Status: {basic.get('trial_status', 'Not specified')}",
                f"Start Date: {basic.get('start_date', 'Not specified')}",
                f"Decision Date: {basic.get('decision_date', 'Not specified')}",
                f"Publish Date: {basic.get('publish_date', 'Not specified')}",
            ]
        )
    if details:
        summary_parts.extend(
            [
                "=== TRIAL DETAILS ===",
                f"Title: {details.get('full_title', 'Not specified')}",
                f"Category: {details.get('trial_category', 'Not specified')}",
                "\nTrial Objectives:",
                f"Main Objective: {details.get('trial_objective', {}).get('main_objective', 'Not specified')}",
                "\nSecondary Objectives:",
                *[
                    f"- {obj}"
                    for obj in details.get("trial_objective", {}).get(
                        "secondary_objective", ["None specified"]
                    )
                ],
                "\nTrial Scopes:",
                *[
                    f"- {scope}"
                    for scope in details.get("trial_objective", {}).get(
                        "trial_scopes", ["None specified"]
                    )
                ],
                "\nMedical Information:",
                "\nMedical Conditions:",
                *[
                    f"- {cond}"
                    for cond in details.get("medical_conditions", ["None specified"])
                ],
                "\nMedDRA Terms:",
                *[
                    f"- {term}"
                    for term in details.get("meddra_terms", ["None specified"])
                ],
                "\nCriteria:",
                "\nInclusion Criteria:",
                *[
                    f"- {crit}"
                    for crit in details.get("inclusion_criteria", ["None specified"])
                ],
                "\nExclusion Criteria:",
                *[
                    f"- {crit}"
                    for crit in details.get("exclusion_criteria", ["None specified"])
                ],
                "\nEndpoints:",
                "\nPrimary Endpoints:",
                *[
                    f"- {ep}"
                    for ep in details.get("endpoints", {}).get(
                        "primary", ["None specified"]
                    )
                ],
                "\nSecondary Endpoints:",
                *[
                    f"- {ep}"
                    for ep in details.get("endpoints", {}).get(
                        "secondary", ["None specified"]
                    )
                ],
                "\nTrial Population Information:",
                f"Duration: {details.get('trial_duration', 'Not specified')}",
                f"Population Details: {details.get('population', 'Not specified')}",
                f"Individual Participant Data: {details.get('participant_data', 'Not specified')}",
                "\nAdditional Information:",
                f"Protocol Information: {details.get('protocol_info', 'Not specified')}",
                f"Scientific Advice: {details.get('scientific_advice', 'Not specified')}",
            ]
        )
    if products:
        summary_parts.extend(["\n=== INVESTIGATIONAL PRODUCTS ==="])
        for product in products:
            info = product.get("product_info", {})
            substances = product.get("substances", {})
            summary_parts.extend(
                [
                    f"\nProduct ID: {product.get('id', 'Not specified')}",
                    f"Product Name: {info.get('product_name', 'Not specified')}",
                    f"Display Name: {product.get('product_display_name', 'Not specified')}",
                    f"Product PK: {info.get('product_pk', 'Not specified')}",
                    f"Pharmaceutical Form: {info.get('product_pharm_form', 'Not specified')}",
                    f"Pharmaceutical Form Display: {product.get('pharmaceutical_form_display', 'Not specified')}",
                    f"Other Form: {info.get('pharm_form', 'Not specified')}",
                    f"Authorization Status: {info.get('auth_status', 'Not specified')}",
                    f"Active Substance: {info.get('active_substance_name', 'Not specified')}",
                    f"All Substances/Chemicals: {product.get('all_substances_chemicals', 'Not specified')}",
                    f"JSON Active Substances: {product.get('json_active_substance_names', 'Not specified')}",
                    f"Substances Product PK: {substances.get('product_pk', 'Not specified')}",
                    f"Pediatric Formulation: {product.get('is_paediatric', 'Not specified')}",
                    f"Role in Trial: {product.get('mp_role_in_trial', 'Not specified')}",
                    f"Orphan Drug: {product.get('orphan_drug_edit', 'Not specified')}",
                    "\nDosage Information:",
                    f"- Max Daily Dose: {product.get('dosage', {}).get('max_daily_dose', 'Not specified')}",
                    f"- Dose UOM: {product.get('dosage', {}).get('dose_uom', 'Not specified')}",
                    f"- Max Total Dose: {product.get('dosage', {}).get('max_total_dose', 'Not specified')}",
                    f"- Total Dose UOM: {product.get('dosage', {}).get('dose_uom_total', 'Not specified')}",
                    f"- Treatment Period: {product.get('dosage', {}).get('max_treatment_period', 'Not specified')}",
                    f"- Time Unit: {product.get('dosage', {}).get('time_unit_code', 'Not specified')}",
                    "\nAdditional Information:",
                    f"- Other Medicinal Product: {product.get('other_info', {}).get('other_medicinal_product', 'Not specified')}",
                    "\nDevices:",
                    *[
                        f"- {device}"
                        for device in product.get("devices", ["None specified"])
                    ],
                    "\nCharacteristics:",
                    *[
                        f"- {char}"
                        for char in product.get("characteristics", ["None specified"])
                    ],
                    "\nRoutes:",
                    *[
                        f"- {route}"
                        for route in product.get("routes", ["None specified"])
                    ],
                ]
            )
    if sponsors:
        summary_parts.extend(["\n=== SPONSORS AND CONTACTS ==="])
        for sponsor in sponsors:
            summary_parts.extend(
                [
                    f"\nSponsor: {sponsor.get('name', 'Not specified')}",
                    "\nPublic Contacts:",
                    *[
                        f"- {c.get('org_name', 'Unknown')}: {c.get('email', 'No email')}"
                        for c in sponsor.get("public_contacts", [])
                    ],
                    "\nScientific Contacts:",
                    *[
                        f"- {c.get('org_name', 'Unknown')}: {c.get('email', 'No email')}"
                        for c in sponsor.get("scientific_contacts", [])
                    ],
                    "\nThird Parties:",
                    *[
                        f"- {tp.get('org_name', 'Unknown')} ({tp.get('org_type', 'Unknown')}): {tp.get('email', 'No email')}"
                        for tp in sponsor.get("third_parties", [])
                    ],
                ]
            )
    if category:
        summary_parts.extend(
            [
                "\n=== CATEGORY DETAILS ===",
                f"Trial Category Code: {category.get('trial_category_code', 'Not specified')}",
                f"Trial Category Justification: {category.get('trial_category_justification', 'Not specified')}",
                "\nTherapeutic Areas:",
                *[
                    f"- {area.get('name', 'Unknown')} ({area.get('code', 'No code')})"
                    for area in category.get("therapeutic_areas", [])
                ],
                "\nProduct Roles:",
                *[
                    f"- {role.get('product_role_name', 'Unknown')} ({role.get('product_role_code', 'No code')})"
                    f"{': ' + role.get('comments') if role.get('comments') else ''}"
                    for role in category.get("product_roles", [])
                ],
                f"\nCategory Justification: {category.get('trial_category_justification', 'Not specified')}",
            ]
        )
    if auth_parts:
        summary_parts.extend(["\n=== TRIAL SITES AND STATUS ==="])
        for part in auth_parts:
            summary_parts.extend(
                [
                    f"\nMember State: {part.get('msc_name', 'Not specified')}",
                    f"Trial Status: {part.get('trial_status', 'Not specified')}",
                    f"Recruitment Started: {part.get('recruitment_started', 'Not specified')}",
                    f"Decision Date: {part.get('decision_date', 'Not specified')}",
                    f"Subject Count: {part.get('subject_count', 'Not specified')}",
                    "\nTrial Sites:",
                    *[
                        f"- {site.get('org_name', 'Unknown')} ({site.get('country', 'Unknown')})(Email: {site.get('email', 'No email')})"
                        for site in part.get("trial_sites", [])[:5]
                    ],
                    *(
                        [
                            f"\n[{len(part.get('trial_sites', [])) - 5} more sites not shown]"
                        ]
                        if len(part.get("trial_sites", [])) > 5
                        else []
                    ),
                ]
            )
    if events_docs:
        summary_parts.extend(
            [
                "\n=== EVENTS AND DOCUMENTS ===",
                "\nTrial Events:",
                *[
                    f"- {event.get('msc_name', 'Unknown')}: {event.get('events', 'No events')}"
                    for event in events_docs.get("trial_events", [])
                ],
                "\nDocuments:",
                *[
                    f"- {doc.get('title', 'Unknown')} (UUID: {doc.get('uuid', 'No UUID')})"
                    for doc in events_docs.get("documents", [])[:5]
                ],
                *(
                    [
                        f"\n[{len(events_docs.get('documents', [])) - 5} more documents not shown]"
                    ]
                    if len(events_docs.get("documents", [])) > 5
                    else []
                ),
            ]
        )
    return "\n".join(summary_parts)


def extract_cro_data(data: Dict[str, Any]) -> Dict[str, Any]:

    def safe_extract(
        nested_dict: Dict[str, Any], *keys: str, default: Any = None
    ) -> Any:
        try:
            value = nested_dict
            for key in keys:
                if value is None:
                    return default
                value = value.get(key, default)
            return value
        except (KeyError, TypeError, AttributeError):
            return default

    def extract_list_items(data: Any, *keys: str) -> List[Any]:
        items = safe_extract(data, *keys, default=[])
        return items if isinstance(items, list) else []

    def extract_basic_info() -> Dict[str, Any]:
        return {
            "trial_id": safe_extract(data, "ctNumber"),
            "trial_status": safe_extract(data, "ctStatus"),
            "start_date": safe_extract(data, "startDateEU"),
            "decision_date": safe_extract(data, "decisionDate"),
            "publish_date": safe_extract(data, "publishDate"),
            "public_status_code": safe_extract(data, "ctPublicStatusCode"),
        }

    def extract_countries() -> List[Dict[str, Any]]:
        countries = extract_list_items(
            data, "authorizedApplication", "authorizedPartI", "rowCountriesInfo"
        )
        return [
            {
                "name": safe_extract(country, "name"),
            }
            for country in countries
        ]

    def extract_products() -> List[Dict[str, Any]]:
        products = extract_list_items(
            data, "authorizedApplication", "authorizedPartI", "products"
        )
        return [
            {
                "id": safe_extract(product, "id"),
                "product_info": {
                    "product_pk": safe_extract(
                        product, "productDictionaryInfo", "productPk"
                    ),
                    "product_pharm_form": safe_extract(
                        product, "productDictionaryInfo", "productPharmForm"
                    ),
                    "auth_status": safe_extract(
                        product, "productDictionaryInfo", "prodAuthStatus"
                    ),
                    "product_name": safe_extract(
                        product, "productDictionaryInfo", "prodName"
                    ),
                    "pharm_form": safe_extract(
                        product, "productDictionaryInfo", "pharmForm"
                    ),
                    "active_substance_name": safe_extract(
                        product, "productDictionaryInfo", "activeSubstanceName"
                    ),
                },
                "substances": {
                    "product_pk": safe_extract(
                        product, "productDictionaryInfo", "productSubstances"
                    ),
                },
                "is_paediatric": safe_extract(product, "isPaediatricFormulation"),
                "mp_role_in_trial": safe_extract(product, "mpRoleInTrial"),
                "orphan_drug_edit": safe_extract(product, "orphanDrugEdit"),
                "dosage": {
                    "dose_uom": safe_extract(product, "doseUom"),
                    "max_daily_dose": safe_extract(product, "maxDailyDoseAmount"),
                    "dose_uom_total": safe_extract(product, "doseUomTotal"),
                    "max_total_dose": safe_extract(product, "maxTotalDoseAmount"),
                    "max_treatment_period": safe_extract(product, "maxTreatmentPeriod"),
                    "time_unit_code": safe_extract(product, "timeUnitCode"),
                },
                "other_info": {
                    "other_medicinal_product": safe_extract(
                        product, "otherMedicinalProduct"
                    ),
                },
                "devices": extract_list_items(product, "devices"),
                "characteristics": extract_list_items(product, "characteristics"),
                "routes": extract_list_items(product, "routes"),
                "all_substances_chemicals": safe_extract(
                    product, "allSubstancesChemicals"
                ),
                "product_display_name": safe_extract(product, "productName"),
                "json_active_substance_names": safe_extract(
                    product, "jsonActiveSubstanceNames"
                ),
                "pharmaceutical_form_display": safe_extract(
                    product, "pharmaceuticalFormDisplay"
                ),
            }
            for product in products
        ]

    def extract_trial_details() -> Dict[str, Any]:
        base = safe_extract(
            data, "authorizedApplication", "authorizedPartI", "trialDetails"
        )
        conditions = extract_list_items(
            base, "trialInformation", "medicalCondition", "partIMedicalConditions"
        )
        trial_scopes = extract_list_items(
            base, "trialInformation", "trialObjective", "trialScopes"
        )
        return {
            "full_title": safe_extract(base, "clinicalTrialIdentifiers", "fullTitle"),
            "trial_category": safe_extract(base, "trialInformation", "trialCategory"),
            "medical_conditions": [
                safe_extract(condition, "medicalCondition") for condition in conditions
            ],
            "meddra_terms": extract_list_items(
                base, "trialInformation", "medicalCondition", "meddraConditionTerms"
            ),
            "trial_objective": {
                "trial_scopes": [safe_extract(scope, "code") for scope in trial_scopes],
                "main_objective": safe_extract(
                    base, "trialInformation", "trialObjective", "mainObjective"
                ),
                "secondary_objective": [
                    obj.get("secondaryObjective")
                    for obj in extract_list_items(
                        base,
                        "trialInformation",
                        "trialObjective",
                        "secondaryObjectives",
                    )
                ],
            },
            "inclusion_criteria": [
                crit.get("principalInclusionCriteria")
                for crit in extract_list_items(
                    base,
                    "trialInformation",
                    "eligibilityCriteria",
                    "principalInclusionCriteria",
                )
            ],
            "exclusion_criteria": [
                crit.get("principalExclusionCriteria")
                for crit in extract_list_items(
                    base,
                    "trialInformation",
                    "eligibilityCriteria",
                    "principalExclusionCriteria",
                )
            ],
            "endpoints": {
                "primary": [
                    ep.get("endPoint")
                    for ep in extract_list_items(
                        base, "trialInformation", "endPoint", "primaryEndPoints"
                    )
                ],
                "secondary": [
                    ep.get("endPoint")
                    for ep in extract_list_items(
                        base, "trialInformation", "endPoint", "secondaryEndPoints"
                    )
                ],
            },
            "trial_duration": safe_extract(base, "trialInformation", "trialDuration"),
            "population": safe_extract(
                base, "trialInformation", "populationOfTrialSubjects"
            ),
            "participant_data": safe_extract(
                base, "trialInformation", "individualParticipantData"
            ),
            "protocol_info": safe_extract(base, "protocolInformation"),
            "scientific_advice": safe_extract(base, "scientificAdviceAndPip"),
        }

    def extract_sponsors() -> List[Dict[str, Any]]:
        sponsors = extract_list_items(
            data, "authorizedApplication", "authorizedPartI", "sponsors"
        )
        return [
            {
                "name": safe_extract(sponsor, "organisation", "name"),
                "public_contacts": [
                    {
                        "email": safe_extract(contact, "functionalEmailAddress"),
                        "org_name": safe_extract(contact, "organisation", "name"),
                    }
                    for contact in extract_list_items(sponsor, "publicContacts")
                ],
                "scientific_contacts": [
                    {
                        "email": safe_extract(contact, "functionalEmailAddress"),
                        "org_name": safe_extract(contact, "organisation", "name"),
                    }
                    for contact in extract_list_items(sponsor, "scientificContacts")
                ],
                "third_parties": [
                    {
                        "org_type": safe_extract(
                            party, "organisationAddress", "organisation", "type"
                        ),
                        "org_name": safe_extract(
                            party, "organisationAddress", "organisation", "name"
                        ),
                        "email": safe_extract(party, "organisationAddress", "email"),
                    }
                    for party in extract_list_items(sponsor, "thirdParties")
                ],
            }
            for sponsor in sponsors
        ]

    def extract_category_details() -> Dict[str, Any]:
        base = safe_extract(data, "authorizedApplication", "authorizedPartI")
        therapeutic_areas = extract_list_items(base, "partOneTherapeuticAreas")
        product_roles = extract_list_items(base, "productRoleGroupInfos")

        return {
            "trial_category_code": safe_extract(base, "trialCategoryCode"),
            "trial_category_justification": safe_extract(
                base, "trialCategoryJustificationComment"
            ),
            "therapeutic_areas": [
                {
                    "code": safe_extract(area, "therapeuticArea", "code"),
                    "name": safe_extract(area, "therapeuticArea", "name"),
                }
                for area in therapeutic_areas
            ],
            "product_roles": [
                {
                    "comments": safe_extract(role, "comments"),
                    "product_role_code": safe_extract(role, "productRoleCode"),
                    "product_role_name": safe_extract(role, "productRoleName"),
                }
                for role in product_roles
            ],
        }

    def extract_authorized_parts() -> List[Dict[str, Any]]:
        parts = extract_list_items(data, "authorizedApplication", "authorizedPartsII")
        return [
            {
                "msc_name": safe_extract(part, "mscInfo", "mscName"),
                "trial_status": safe_extract(part, "mscInfo", "trialStatus"),
                "recruitment_started": safe_extract(
                    part, "mscInfo", "hasRecruitmentStarted"
                ),
                "decision_date": safe_extract(part, "decisionDate"),
                "subject_count": safe_extract(part, "recruitmentSubjectCount"),
                "trial_sites": [
                    {
                        "org_name": safe_extract(
                            site, "organisationAddressInfo", "organisation", "name"
                        ),
                        "country": safe_extract(
                            site, "organisationAddressInfo", "address", "countryName"
                        ),
                        "email": safe_extract(site, "organisationAddressInfo", "email"),
                    }
                    for site in extract_list_items(part, "trialSites")
                ],
            }
            for part in parts
        ]

    def extract_events_and_documents() -> Dict[str, Any]:
        return {
            "trial_events": [
                {
                    "msc_name": safe_extract(event, "mscName"),
                    "events": safe_extract(event, "events"),
                }
                for event in extract_list_items(data, "events", "trialEvents")
            ],
            "documents": [
                {"title": safe_extract(doc, "title"), "uuid": safe_extract(doc, "uuid")}
                for doc in extract_list_items(data, "documents")
            ],
        }

    extracted_data = {
        "basic_info": extract_basic_info(),
        "countries": extract_countries(),
        "products": extract_products(),
        "trial_details": extract_trial_details(),
        "sponsors": extract_sponsors(),
        "category_details": extract_category_details(),
        "authorized_parts": extract_authorized_parts(),
        "events_and_documents": extract_events_and_documents(),
    }

    summary = format_detailed_trial_summary(extracted_data)
    extracted_data["summary"] = summary

    return extracted_data


############################################################################################################
##clinicaltrials.gov parsers


def format_ct_gov_study_summary(study: Dict[str, Any]) -> str:
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    nct_id = identification.get("nctId", "")
    title = identification.get("briefTitle", "")
    status = protocol.get("statusModule", {}).get("overallStatus", "")
    conditions = protocol.get("conditionsModule", {}).get("conditions", [])
    summary = protocol.get("descriptionModule", {}).get("briefSummary", "")
    formatted = f"NCT ID: {nct_id}\n"
    formatted += f"Title: {title}\n"
    formatted += f"Status: {status}\n"
    formatted += f"Conditions: {', '.join(conditions)}\n"
    formatted += f"Summary: {summary}\n"
    return formatted


def format_ct_gov_study_batch(studies: List[Dict[str, Any]]) -> str:
    if not studies:
        return "No studies found."
    result = "### Clinical Trial Search Results\n\n"
    for i, study in enumerate(studies, 1):
        result += f"## Study {i}\n"
        result += format_ct_gov_study_summary(study) + "\n\n"
    return result


def format_ctgov_trial_details(study_data: dict) -> str:
    try:
        protocol = study_data.get("protocolSection", {})
        results = study_data.get("resultsSection", {})

        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        sponsor = protocol.get("sponsorCollaboratorsModule", {})
        design = protocol.get("designModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        outcomes = protocol.get("outcomesModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        description = protocol.get("descriptionModule", {})
        conditions = protocol.get("conditionsModule", {})

        participant_flow = results.get("participantFlowModule", {})
        outcome_results = results.get("outcomeMeasuresModule", {})
        adverse = results.get("adverseEventsModule", {})

        result = (
            f"# Clinical Trial Details: {identification.get('nctId', 'Unknown ID')}\n\n"
        )

        result += "## Trial Identification and Status\n\n"
        result += f"**Trial ID**: {identification.get('nctId', 'Not provided')}\n"
        result += f"**Title**: {identification.get('officialTitle', identification.get('briefTitle', 'Not provided'))}\n"
        result += f"**Status**: {status.get('overallStatus', 'Not provided')}\n"
        result += f"**Started**: {status.get('startDateStruct', {}).get('date', 'Not provided')}\n"
        result += f"**Primary Completion**: {status.get('primaryCompletionDateStruct', {}).get('date', 'Not provided')}\n"

        result += "\n## Sponsor and Collaborator Information\n\n"
        result += f"**Lead Sponsor**: {sponsor.get('leadSponsor', {}).get('name', 'Not provided')} ({sponsor.get('leadSponsor', {}).get('class', 'Unknown')})\n"

        if conditions:
            result += "\n## Conditions and Keywords\n\n"
            if conditions.get("conditions"):
                result += (
                    "**Conditions**: "
                    + ", ".join(conditions.get("conditions", []))
                    + "\n"
                )

        result += "\n## Study Design\n\n"
        if design:
            result += f"**Study Type**: {design.get('studyType', 'Not provided')}\n"
            if design.get("phases"):
                result += (
                    f"**Phase**: {', '.join(design.get('phases', ['Not provided']))}\n"
                )

            design_info = design.get("designInfo", {})
            if design_info:
                for k, v in design_info.items():
                    if v:
                        result += f"**{k.capitalize()}**: {v}\n"

            result += f"**Target Duration**: {design.get('targetDuration', 'Not specified')}\n"
            result += f"**Enrollment**: {design.get('enrollmentInfo', {}).get('count', 'Not specified')} ({design.get('enrollmentInfo', {}).get('type', 'Not specified')})\n"

            if design.get("studyType") == "OBSERVATIONAL":
                result += f"**Observational Model**: {design.get('designInfo', {}).get('observationalModel', 'Not specified')}\n"
                result += f"**Time Perspective**: {design.get('designInfo', {}).get('timePerspective', 'Not specified')}\n"

        if arms:
            result += "\n## Arms and Interventions\n\n"
            for arm in arms.get("arms", []):
                result += f"### Arm: {arm.get('label', 'Unnamed Arm')}\n"
                result += f"**Type**: {arm.get('type', 'Not specified')}\n"
                result += f"**Description**: {arm.get('description', 'No description provided')}\n"
                if arm.get("interventionNames"):
                    result += f"**Interventions**: {', '.join(arm.get('interventionNames', []))}\n\n"

            if arms.get("interventions"):
                result += "### Detailed Interventions\n\n"
                for intervention in arms.get("interventions", []):
                    result += f"**{intervention.get('type', 'Unknown Type')}**: {intervention.get('name', 'Unnamed')}\n"
                    result += f"**Description**: {intervention.get('description', 'No description provided')}\n"
                    if intervention.get("armGroupLabels"):
                        result += f"**Arms**: {', '.join(intervention.get('armGroupLabels', []))}\n\n"

        if outcomes:
            result += "\n## Outcome Measures\n\n"

            if outcomes.get("primaryOutcomes"):
                result += "### Primary Outcomes\n\n"
                for outcome in outcomes.get("primaryOutcomes", []):
                    result += (
                        f"- **Measure**: {outcome.get('measure', 'Not specified')}\n"
                    )
                    result += f"  **Time Frame**: {outcome.get('timeFrame', 'Not specified')}\n"
                    if outcome.get("description"):
                        result += f"  **Description**: {outcome.get('description')}\n"
                    result += "\n"

            if outcomes.get("secondaryOutcomes"):
                result += "### Secondary Outcomes\n\n"
                for outcome in outcomes.get("secondaryOutcomes", []):
                    result += (
                        f"- **Measure**: {outcome.get('measure', 'Not specified')}\n"
                    )
                    result += f"  **Time Frame**: {outcome.get('timeFrame', 'Not specified')}\n"
                    if outcome.get("description"):
                        result += f"  **Description**: {outcome.get('description')}\n"
                    result += "\n"

        if eligibility:
            result += "\n## Eligibility\n\n"
            result += (
                f"**Minimum Age**: {eligibility.get('minimumAge', 'Not specified')}\n"
            )
            result += (
                f"**Maximum Age**: {eligibility.get('maximumAge', 'Not specified')}\n"
            )
            result += f"**Sex**: {eligibility.get('sex', 'Not specified')}\n"
            result += f"**Gender**: {eligibility.get('gender', 'Not specified')}\n"

            if eligibility.get("stdAges"):
                result += (
                    f"**Standard Ages**: {', '.join(eligibility.get('stdAges', []))}\n"
                )

            if eligibility.get("healthyVolunteers") is not None:
                result += f"**Accepts Healthy Volunteers**: {'Yes' if eligibility.get('healthyVolunteers') else 'No'}\n"

            if eligibility.get("studyPopulation"):
                result += (
                    f"**Study Population**: {eligibility.get('studyPopulation')}\n"
                )

            if eligibility.get("samplingMethod"):
                result += f"**Sampling Method**: {eligibility.get('samplingMethod')}\n"

            if eligibility.get("criteria"):
                result += "\n### Inclusion/Exclusion Criteria\n\n"
                result += eligibility.get("criteria", "Not provided")
                result += "\n"

        if description:
            result += "\n## Study Description\n\n"
            if description.get("briefSummary"):
                result += "### Brief Summary\n\n"
                result += description.get("briefSummary", "Not provided")
                result += "\n\n"

            if description.get("detailedDescription"):
                result += "### Detailed Description\n\n"
                result += description.get("detailedDescription", "Not provided")
                result += "\n\n"

        if results:
            result += "\n# Study Results\n\n"

            if participant_flow:
                result += "## Participant Flow\n\n"

                if participant_flow.get("preAssignmentDetails"):
                    result += (
                        "**Pre-assignment Details**: "
                        + participant_flow.get("preAssignmentDetails")
                        + "\n\n"
                    )

                if participant_flow.get("recruitmentDetails"):
                    result += (
                        "**Recruitment Details**: "
                        + participant_flow.get("recruitmentDetails")
                        + "\n\n"
                    )

                if participant_flow.get("groups"):
                    result += "### Study Groups\n\n"
                    for group in participant_flow.get("groups", []):
                        result += f"- **{group.get('title', 'Unnamed')}**: {group.get('description', 'No description')}\n"
                    result += "\n"

                if participant_flow.get("periods"):
                    result += "### Flow Periods\n\n"
                    for period in participant_flow.get("periods", []):
                        result += f"**{period.get('title', 'Unnamed Period')}**:\n\n"

                        if period.get("milestones"):
                            result += "**Milestones**:\n\n"
                            for milestone in period.get("milestones", []):
                                result += f"- {milestone.get('type', 'Unnamed')}: "
                                achievements = []
                                for achievement in milestone.get("achievements", []):
                                    group_id = achievement.get("groupId")
                                    num = achievement.get("numSubjects", "0")
                                    group_name = next(
                                        (
                                            g.get("title")
                                            for g in participant_flow.get("groups", [])
                                            if g.get("id") == group_id
                                        ),
                                        group_id,
                                    )
                                    achievements.append(f"{group_name}: {num}")
                                result += ", ".join(achievements) + "\n"
                            result += "\n"

                        if period.get("dropWithdraws"):
                            result += "**Dropouts/Withdrawals**:\n\n"
                            for dropout in period.get("dropWithdraws", []):
                                result += f"- {dropout.get('type', 'Unnamed')}: "
                                reasons = []
                                for reason in dropout.get("reasons", []):
                                    group_id = reason.get("groupId")
                                    num = reason.get("numSubjects", "0")
                                    group_name = next(
                                        (
                                            g.get("title")
                                            for g in participant_flow.get("groups", [])
                                            if g.get("id") == group_id
                                        ),
                                        group_id,
                                    )
                                    reasons.append(f"{group_name}: {num}")
                                result += ", ".join(reasons) + "\n"
                            result += "\n"

            if outcome_results and outcome_results.get("outcomeMeasures"):
                result += "## Outcome Results\n\n"

                for i, outcome in enumerate(
                    outcome_results.get("outcomeMeasures", []), 1
                ):
                    if i > 3:
                        result += "*(Additional outcome measures available but not shown)*\n\n"
                        break

                    result += f"### {outcome.get('type', 'Outcome')} Outcome: {outcome.get('title', 'Unnamed')}\n\n"

                    if outcome.get("description"):
                        result += f"**Description**: {outcome.get('description')}\n"

                    if outcome.get("timeFrame"):
                        result += f"**Time Frame**: {outcome.get('timeFrame')}\n"

                    if outcome.get("classes"):
                        result += "\n**Results**:\n\n"

                        for cls in outcome.get("classes", []):
                            for cat in cls.get("categories", []):
                                for measurement in cat.get("measurements", []):
                                    group_id = measurement.get("groupId")
                                    group_name = next(
                                        (
                                            g.get("title")
                                            for g in outcome.get("groups", [])
                                            if g.get("id") == group_id
                                        ),
                                        group_id,
                                    )
                                    value = measurement.get("value", "")

                                    result += f"- {group_name}: {value} {outcome.get('unitOfMeasure', '')}\n"

                        result += "\n"

                    if outcome.get("analyses"):
                        result += "**Statistical Analysis**:\n\n"

                        for analysis in outcome.get("analyses", []):
                            method = analysis.get("statisticalMethod", "")
                            param_type = analysis.get("paramType", "")
                            param_value = analysis.get("paramValue", "")
                            p_value = analysis.get("pValue", "")

                            result += f"- Method: {method}\n"
                            result += f"  {param_type}: {param_value}\n"

                            if p_value:
                                result += f"  p-value: {p_value}\n"

                            if analysis.get("ciPctValue"):
                                result += f"  {analysis.get('ciPctValue')}% CI: [{analysis.get('ciLowerLimit', '')}, {analysis.get('ciUpperLimit', '')}]\n"

                            result += "\n"

            if adverse:
                result += "## Adverse Events Summary\n\n"

                if adverse.get("description"):
                    result += f"**Description**: {adverse.get('description')}\n\n"

                if adverse.get("eventGroups"):
                    result += "### Event Groups\n\n"

                    for group in adverse.get("eventGroups", []):
                        result += f"- **{group.get('title', 'Unnamed')}**:\n"

                        serious_affected = group.get("seriousNumAffected", 0)
                        serious_at_risk = group.get("seriousNumAtRisk", 0)

                        if serious_at_risk:
                            result += f"  Serious Events: {serious_affected}/{serious_at_risk} participants\n"

                        other_affected = group.get("otherNumAffected", 0)
                        other_at_risk = group.get("otherNumAtRisk", 0)

                        if other_at_risk:
                            result += f"  Other Events: {other_affected}/{other_at_risk} participants\n"

                    result += "\n"

        return result

    except Exception as e:
        return f"Error formatting trial details: {str(e)}\n\nRaw data:\n{json.dumps(study_data, indent=2)[:5000]}..."
