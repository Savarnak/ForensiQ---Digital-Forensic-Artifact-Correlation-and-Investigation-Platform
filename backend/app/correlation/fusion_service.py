import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.knowledge_graph.graph_builder import KnowledgeGraphBuilder, NODE_TYPES, RELATIONSHIP_TYPES
from app.core.logging import logger

CORRELATION_DISCLAIMER = "Evidence-backed correlation for investigator review. Correlation does not prove identity or guilt."

class IntelligenceFusionService:
    """Core Intelligence Fusion Service performing entity resolution, relationship detection, 
    7 correlation pattern checks, timeline construction, and Neo4j graph syncing."""

    @staticmethod
    def resolve_entities(raw_findings: List[Dict[str, Any]], evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolves raw tool findings and evidence items into canonical entity graph nodes."""
        nodes_dict: Dict[str, Dict[str, Any]] = {}

        # 1. Evidence Nodes
        for ev in evidence_items:
            ev_id = str(ev.get("id", "ev_unknown"))
            ev_name = ev.get("file_name", "Evidence File")
            nodes_dict[f"ev_{ev_id}"] = KnowledgeGraphBuilder.create_node(
                node_id=f"ev_{ev_id}",
                label="Evidence",
                name=ev_name,
                properties={"file_type": ev.get("file_type"), "file_path": ev.get("file_path")}
            )

        # 2. Findings & Entity Resolution
        for finding in raw_findings:
            tool_name = finding.get("tool_name", "")
            data = finding.get("content", {})

            # Handles (Social / Chat Handles)
            handles = data.get("handles", [])
            if not handles and "entities" in data and isinstance(data["entities"], list):
                handles = [e["value"] for e in data["entities"] if isinstance(e, dict) and e.get("type") == "HANDLE"]
            for h in handles:
                val = str(h)
                clean_h = re.sub(r'[^a-zA-Z0-9_]', '_', val).strip('_').lower()
                if clean_h and len(clean_h) >= 3 and not clean_h.isdigit():
                    acc_id = f"account_{clean_h}"
                    person_id = f"person_{clean_h}"
                    nodes_dict[acc_id] = KnowledgeGraphBuilder.create_node(acc_id, "Account", val, {"platform": "Social/Chat"})
                    nodes_dict[person_id] = KnowledgeGraphBuilder.create_node(person_id, "Person", f"Identity ({val})", {"handle": val})

            # Phone Numbers
            phones = data.get("phone_numbers", [])
            if not phones and "entities" in data and isinstance(data["entities"], list):
                phones = [e["value"] for e in data["entities"] if isinstance(e, dict) and e.get("type") == "PHONE"]
            for p in phones:
                val = str(p)
                clean_p = re.sub(r'[^0-9]', '', val)
                if clean_p and len(clean_p) >= 7 and not clean_p.startswith("2026"):
                    p_id = f"account_phone_{clean_p}"
                    nodes_dict[p_id] = KnowledgeGraphBuilder.create_node(p_id, "Account", val, {"identifier_type": "PHONE"})

            # Emails
            emails = data.get("emails", [])
            if not emails and "entities" in data and isinstance(data["entities"], list):
                emails = [e["value"] for e in data["entities"] if isinstance(e, dict) and e.get("type") == "EMAIL"]
            for em in emails:
                val = str(em)
                clean_em = re.sub(r'[^a-zA-Z0-9_]', '_', val).strip('_').lower()
                if clean_em:
                    em_id = f"account_email_{clean_em}"
                    nodes_dict[em_id] = KnowledgeGraphBuilder.create_node(em_id, "Account", val, {"identifier_type": "EMAIL"})

            # IPs & Wallets
            ips = data.get("ip_addresses", [])
            for ip in ips:
                val = str(ip)
                clean_ip = re.sub(r'[^0-9_]', '_', val)
                ip_id = f"account_ip_{clean_ip}"
                nodes_dict[ip_id] = KnowledgeGraphBuilder.create_node(ip_id, "Account", val, {"identifier_type": "IP_ADDRESS"})

            # Devices
            devices = data.get("devices", [])
            if "device_model" in data and data["device_model"]:
                devices.append(data["device_model"])
            if "device_id" in data and data["device_id"]:
                devices.append(data["device_id"])
            for d in devices:
                val = str(d)
                clean_d = re.sub(r'[^a-zA-Z0-9_]', '_', val).strip('_').lower()
                if clean_d:
                    dev_id = f"device_{clean_d}"
                    nodes_dict[dev_id] = KnowledgeGraphBuilder.create_node(dev_id, "Device", val, {"model": val})

            # Locations / GPS
            gps = data.get("gps_coordinates")
            if gps:
                loc_id = f"loc_{gps['latitude']}_{gps['longitude']}"
                loc_name = f"GPS ({gps['latitude']}, {gps['longitude']})"
                nodes_dict[loc_id] = KnowledgeGraphBuilder.create_node(loc_id, "Location", loc_name, {"latitude": gps["latitude"], "longitude": gps["longitude"]})
                
            locations = data.get("locations", [])
            for loc in locations:
                val = str(loc)
                clean_loc = re.sub(r'[^a-zA-Z0-9_]', '_', val).strip('_').lower()
                if clean_loc:
                    loc_id = f"loc_{clean_loc}"
                    nodes_dict[loc_id] = KnowledgeGraphBuilder.create_node(loc_id, "Location", val, {"name": val})

            # Events
            events = data.get("events", [])
            for evt in events:
                if isinstance(evt, dict):
                    evt_id_str = str(evt.get("event_id") or evt.get("title") or "evt")
                    clean_evt = re.sub(r'[^a-zA-Z0-9_]', '_', evt_id_str).strip('_').lower()
                    if clean_evt:
                        e_id = f"event_{clean_evt}"
                        nodes_dict[e_id] = KnowledgeGraphBuilder.create_node(e_id, "Event", evt.get("title") or evt_id_str, {"event_type": evt.get("event_type", "EVENT")})

        return list(nodes_dict.values())

    @staticmethod
    def detect_relationships_and_correlations(
        raw_findings: List[Dict[str, Any]],
        evidence_items: List[Dict[str, Any]],
        nodes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detects evidence-backed relationships across 7 correlation patterns."""
        edges: List[Dict[str, Any]] = []
        correlations: List[Dict[str, Any]] = []
        timeline_events: List[Dict[str, Any]] = []
        contradictions: List[Dict[str, Any]] = []

        node_map = {n["id"]: n for n in nodes}

        # Track appearances per entity across evidence
        entity_evidence_map: Dict[str, List[str]] = {}
        location_events_map: Dict[str, List[Dict[str, Any]]] = {}
        timestamp_events_map: Dict[str, List[Dict[str, Any]]] = {}
        device_accounts_map: Dict[str, List[str]] = {}
        identifier_appearances_map: Dict[str, List[str]] = {}

        for finding in raw_findings:
            tool_name = finding.get("tool_name", "")
            data = finding.get("content", {})
            ev_id = finding.get("evidence_id")
            source_ev = finding.get("provenance", {}).get("source_evidence", "Evidence File")
            ev_ref = {"evidence_id": ev_id, "file_name": source_ev, "tool_name": tool_name}
            ev_node_id = f"ev_{ev_id}" if ev_id else None

            # Ingest handles from finding content
            handles = data.get("handles", [])
            if not handles and "entities" in data and isinstance(data["entities"], list):
                handles = [e["value"] for e in data["entities"] if isinstance(e, dict) and e.get("type") == "HANDLE"]

            for h in handles:
                val = str(h)
                clean_h = re.sub(r'[^a-zA-Z0-9_]', '_', val).strip('_').lower()
                if clean_h and len(clean_h) >= 3 and not clean_h.isdigit():
                    acc_id = f"account_{clean_h}"
                    person_id = f"person_{clean_h}"

                    entity_evidence_map.setdefault(f"HANDLE:{val}", []).append(source_ev)
                    identifier_appearances_map.setdefault(val, []).append(source_ev)

                    # Account ASSOCIATED_WITH Person
                    if acc_id in node_map and person_id in node_map:
                        edges.append(KnowledgeGraphBuilder.create_relationship(
                            source_id=acc_id,
                            target_id=person_id,
                            rel_type="ASSOCIATED_WITH",
                            confidence=0.95,
                            supporting_evidence=[ev_ref]
                        ))

                    # Account MENTIONED_IN Evidence
                    if ev_node_id and ev_node_id in node_map and acc_id in node_map:
                        edges.append(KnowledgeGraphBuilder.create_relationship(
                            source_id=acc_id,
                            target_id=ev_node_id,
                            rel_type="MENTIONED_IN",
                            confidence=0.95,
                            supporting_evidence=[ev_ref]
                        ))

            # Cross-handle communications
            if len(handles) >= 2:
                for i in range(len(handles)):
                    for j in range(i + 1, len(handles)):
                        c1 = re.sub(r'[^a-zA-Z0-9_]', '_', str(handles[i])).strip('_').lower()
                        c2 = re.sub(r'[^a-zA-Z0-9_]', '_', str(handles[j])).strip('_').lower()
                        acc1 = f"account_{c1}"
                        acc2 = f"account_{c2}"
                        if acc1 in node_map and acc2 in node_map and acc1 != acc2:
                            edges.append(KnowledgeGraphBuilder.create_relationship(
                                source_id=acc1,
                                target_id=acc2,
                                rel_type="COMMUNICATED_WITH",
                                confidence=0.92,
                                supporting_evidence=[ev_ref]
                            ))

            # Phones
            phones = data.get("phone_numbers", [])
            if not phones and "entities" in data and isinstance(data["entities"], list):
                phones = [e["value"] for e in data["entities"] if isinstance(e, dict) and e.get("type") == "PHONE"]
            for p in phones:
                val = str(p)
                clean_p = re.sub(r'[^0-9]', '', val)
                if clean_p and len(clean_p) >= 7 and not clean_p.startswith("2026"):
                    p_id = f"account_phone_{clean_p}"
                    if p_id in node_map:
                        for h in handles:
                            clean_h = re.sub(r'[^a-zA-Z0-9_]', '_', str(h)).strip('_').lower()
                            acc_id = f"account_{clean_h}"
                            if acc_id in node_map:
                                edges.append(KnowledgeGraphBuilder.create_relationship(
                                    source_id=acc_id,
                                    target_id=p_id,
                                    rel_type="ASSOCIATED_WITH",
                                    confidence=0.90,
                                    supporting_evidence=[ev_ref]
                                ))

            # Devices
            devices = data.get("devices", [])
            if "device_model" in data and data["device_model"]:
                devices.append(data["device_model"])
            if "device_id" in data and data["device_id"]:
                devices.append(data["device_id"])
            for d in devices:
                val = str(d)
                clean_d = re.sub(r'[^a-zA-Z0-9_]', '_', val).strip('_').lower()
                dev_id = f"device_{clean_d}"
                if dev_id in node_map:
                    for h in handles:
                        clean_h = re.sub(r'[^a-zA-Z0-9_]', '_', str(h)).strip('_').lower()
                        person_id = f"person_{clean_h}"
                        if person_id in node_map:
                            edges.append(KnowledgeGraphBuilder.create_relationship(
                                source_id=person_id,
                                target_id=dev_id,
                                rel_type="USES",
                                confidence=0.90,
                                supporting_evidence=[ev_ref]
                            ))
                    if ev_node_id and ev_node_id in node_map:
                        edges.append(KnowledgeGraphBuilder.create_relationship(
                            source_id=ev_node_id,
                            target_id=dev_id,
                            rel_type="SUPPORTED_BY",
                            confidence=0.95,
                            supporting_evidence=[ev_ref]
                        ))

            # Locations / GPS
            gps = data.get("gps_coordinates")
            dt = data.get("datetime_original")
            if gps:
                loc_id = f"loc_{gps['latitude']}_{gps['longitude']}"
                if loc_id in node_map and ev_node_id and ev_node_id in node_map:
                    edges.append(KnowledgeGraphBuilder.create_relationship(
                        source_id=ev_node_id,
                        target_id=loc_id,
                        rel_type="LOCATED_AT",
                        confidence=0.95,
                        supporting_evidence=[ev_ref]
                    ))
                if gps and dt:
                    loc_label = f"GPS ({gps['latitude']}, {gps['longitude']})"
                    timeline_events.append({
                        "timestamp": dt,
                        "title": "EXIF Geotag Capture",
                        "description": f"Evidence '{source_ev}' captured at {loc_label}",
                        "source_evidence": source_ev,
                        "location": loc_label
                    })
                    location_events_map.setdefault(loc_label, []).append({"timestamp": dt, "source": source_ev})
                    timestamp_events_map.setdefault(dt, []).append({"location": loc_label, "source": source_ev})

            # 3. TimelineExtractor Events
            elif tool_name == "TimelineExtractor":
                events = data.get("timeline_events", [])
                for ev in events:
                    if isinstance(ev, dict) and ev.get("timestamp"):
                        ts = ev["timestamp"]
                        timeline_events.append({
                            "timestamp": ts,
                            "title": "Extracted Timeline Event",
                            "description": ev.get("context", "Event sequence extracted"),
                            "source_evidence": source_ev
                        })
                        timestamp_events_map.setdefault(ts, []).append({"source": source_ev, "context": ev.get("context")})

        # --- EVALUATE 7 CORRELATION PATTERNS ---

        # Pattern 1: Same Entity Appearing Across Evidence
        for entity_key, sources in entity_evidence_map.items():
            unique_sources = list(set(sources))
            if len(unique_sources) >= 2:
                etype, val = entity_key.split(":", 1)
                correlations.append({
                    "pattern": "SAME_ENTITY_ACROSS_EVIDENCE",
                    "title": f"Repeated {etype} Discovery: '{val}'",
                    "description": f"Entity '{val}' ({etype}) identified across {len(unique_sources)} distinct evidence sources: {', '.join(unique_sources)}.",
                    "entity": val,
                    "evidence_sources": unique_sources,
                    "confidence": 0.95,
                    "disclaimer": CORRELATION_DISCLAIMER
                })

        # Pattern 2: Shared Device
        for dev_node in [n for n in nodes if n.get("label") == "Device"]:
            dev_name = dev_node["name"]
            related_accounts = [e["source"] for e in edges if e["target"] == dev_node["id"] and e["relationship"] == "USES"]
            correlations.append({
                "pattern": "SHARED_DEVICE",
                "title": f"Device Hardware Link: {dev_name}",
                "description": f"Device '{dev_name}' cross-referenced with evidence metadata and associated user activity.",
                "device": dev_name,
                "confidence": 0.92,
                "disclaimer": CORRELATION_DISCLAIMER
            })

        # Pattern 3: Shared Location
        for loc_label, events in location_events_map.items():
            sources = list(set(e["source"] for e in events))
            if len(sources) >= 1:
                correlations.append({
                    "pattern": "SHARED_LOCATION",
                    "title": f"Geographic Hotspot Correlation: {loc_label}",
                    "description": f"Location '{loc_label}' confirmed across {len(sources)} evidence items ({', '.join(sources)}).",
                    "location": loc_label,
                    "evidence_sources": sources,
                    "confidence": 0.95,
                    "disclaimer": CORRELATION_DISCLAIMER
                })

        # Pattern 4: Temporal Correlation
        for ts, events in timestamp_events_map.items():
            if len(events) >= 2:
                sources = list(set(e["source"] for e in events))
                correlations.append({
                    "pattern": "TEMPORAL_CORRELATION",
                    "title": f"Shared Timestamp Convergence: {ts}",
                    "description": f"Timestamp '{ts}' shared across multiple artifacts ({', '.join(sources)}).",
                    "timestamp": ts,
                    "evidence_sources": sources,
                    "confidence": 0.90,
                    "disclaimer": CORRELATION_DISCLAIMER
                })

        # Pattern 5: Repeated Account
        accounts = [n["name"] for n in nodes if n.get("label") == "Account"]
        account_counts = {acc: sum(1 for e in entity_evidence_map.keys() if acc in e) for acc in set(accounts)}
        for acc, count in account_counts.items():
            if count >= 1:
                correlations.append({
                    "pattern": "REPEATED_ACCOUNT",
                    "title": f"Primary Account Focus: {acc}",
                    "description": f"Account handle '{acc}' repeatedly referenced across evidence corpus.",
                    "account": acc,
                    "confidence": 0.92,
                    "disclaimer": CORRELATION_DISCLAIMER
                })

        # Pattern 6: Repeated Identifier
        for ident, sources in identifier_appearances_map.items():
            unique_sources = list(set(sources))
            if len(unique_sources) >= 2:
                correlations.append({
                    "pattern": "REPEATED_IDENTIFIER",
                    "title": f"Cross-Source Identifier Linkage: '{ident}'",
                    "description": f"Identifier '{ident}' detected across {len(unique_sources)} evidence files: {', '.join(unique_sources)}.",
                    "identifier": ident,
                    "evidence_sources": unique_sources,
                    "confidence": 0.94,
                    "disclaimer": CORRELATION_DISCLAIMER
                })

        # Pattern 7: Conflicting Timestamps / Anomaly Detection
        # Check for near-identical timestamps with conflicting location labels
        timestamps_list = sorted(list(timestamp_events_map.keys()))
        for i in range(len(timestamps_list) - 1):
            ts1 = timestamps_list[i]
            ts2 = timestamps_list[i+1]
            try:
                dt1 = datetime.fromisoformat(ts1.replace("Z", "+00:00"))
                dt2 = datetime.fromisoformat(ts2.replace("Z", "+00:00"))
                time_diff = abs((dt2 - dt1).total_seconds())
                
                locs1 = set(e.get("location") for e in timestamp_events_map[ts1] if e.get("location"))
                locs2 = set(e.get("location") for e in timestamp_events_map[ts2] if e.get("location"))

                if time_diff <= 300 and locs1 and locs2 and locs1 != locs2:
                    contradictions.append({
                        "pattern": "CONFLICTING_TIMESTAMPS",
                        "title": f"Anomalous Location Shift Between {ts1} and {ts2}",
                        "description": f"Device reported locations '{list(locs1)[0]}' and '{list(locs2)[0]}' within {time_diff:.0f} seconds.",
                        "time_difference_sec": time_diff,
                        "locations": [list(locs1)[0], list(locs2)[0]],
                        "confidence": 0.88,
                        "disclaimer": CORRELATION_DISCLAIMER
                    })
            except Exception:
                pass

        # Sort timeline chronologically
        sorted_timeline = sorted(timeline_events, key=lambda x: str(x.get("timestamp", "")))

        # De-duplicate edges
        unique_edges = list({f"{e['source']}_{e['target']}_{e['relationship']}": e for e in edges}.values())

        return {
            "nodes": nodes,
            "edges": unique_edges,
            "correlations": correlations,
            "timeline_events": sorted_timeline,
            "contradictions": contradictions
        }

    @classmethod
    async def correlate_state_findings(cls, state: Any) -> Any:
        """Integration method for ARGUS orchestrator correlator node."""
        raw_findings = state.raw_findings
        evidence_items = state.evidence_items

        # 1. Entity Resolution
        resolved_nodes = cls.resolve_entities(raw_findings, evidence_items)

        # 2. Relationship Detection & 7 Correlation Patterns
        fusion_results = cls.detect_relationships_and_correlations(raw_findings, evidence_items, resolved_nodes)

        # Update CaseState
        state.knowledge_graph_nodes = fusion_results["nodes"]
        state.knowledge_graph_edges = fusion_results["edges"]
        state.timeline_events = fusion_results["timeline_events"]
        state.evidence_contradictions = fusion_results["contradictions"]

        # Sync to Neo4j if available
        await KnowledgeGraphBuilder.sync_to_neo4j(fusion_results["nodes"], fusion_results["edges"])

        logger.info(f"Intelligence Fusion complete: {len(resolved_nodes)} nodes, {len(fusion_results['edges'])} edges, "
                    f"{len(fusion_results['correlations'])} correlations, {len(fusion_results['timeline_events'])} timeline events.")

        return state
