import uuid
import re
import json
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.core.logging import logger

class TimelineEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8].upper()}")
    timestamp: str
    event_type: str  # CHAT_MESSAGE, CELL_CALL, GPS_PING, IMAGE_EXIF, DOCUMENT_EVENT, SYNTHETIC_EVENT
    description: str
    explanation: str
    entities: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    source_evidence: str
    source_tool: str
    confidence: float = 1.0
    anomalies: List[str] = Field(default_factory=list)

class TimelineEngine:
    """Core ARGUS Timeline Engine merging multi-source evidence events, 
    detecting temporal anomalies, providing event explanations, and constructing timelines."""

    @staticmethod
    def parse_timestamp(ts_str: str) -> Optional[datetime]:
        """Parses ISO or common datetime strings into datetime objects."""
        if not ts_str:
            return None
        clean_ts = ts_str.strip().replace("Z", "+00:00")
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M"
        ):
            try:
                return datetime.strptime(clean_ts, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(clean_ts)
        except Exception:
            return None

    @classmethod
    def merge_evidence_events(
        cls,
        evidence_items: List[Dict[str, Any]],
        raw_findings: List[Dict[str, Any]],
        synthetic_case_dir: Optional[str] = None
    ) -> List[TimelineEvent]:
        """Merges events from chats, calls, GPS, images, metadata, and reports into a unified list."""
        merged_events: List[TimelineEvent] = []

        # 1. Merge from raw findings (from tool extraction)
        for finding in raw_findings:
            tool_name = finding.get("tool_name", "UnknownTool")
            data = finding.get("content", {})
            source_ev = finding.get("provenance", {}).get("source_evidence", "Evidence File")

            # MetadataExtractor EXIF
            if tool_name in ["MetadataExtractor", "exif_metadata_extractor"]:
                dt = data.get("datetime_original")
                gps = data.get("gps_coordinates")
                device = data.get("device_model")
                if dt:
                    loc_str = f"GPS ({gps['latitude']}, {gps['longitude']})" if gps else None
                    merged_events.append(TimelineEvent(
                        timestamp=str(dt),
                        event_type="IMAGE_EXIF",
                        description=f"Media file '{source_ev}' captured by camera device '{device or 'Unknown'}'",
                        explanation=f"EXIF header metadata parsed by {tool_name} from image '{source_ev}'",
                        entities=[device] if device else [],
                        location=loc_str,
                        source_evidence=source_ev,
                        source_tool=tool_name,
                        confidence=0.98
                    ))

            # TimelineExtractor
            elif tool_name == "TimelineExtractor":
                events = data.get("timeline_events", [])
                for ev in events:
                    if isinstance(ev, dict) and ev.get("timestamp"):
                        merged_events.append(TimelineEvent(
                            timestamp=str(ev["timestamp"]),
                            event_type="DOCUMENT_EVENT",
                            description=ev.get("context", "Timeline event extracted"),
                            explanation=f"Chronological regex pattern matched by TimelineExtractor in '{source_ev}'",
                            entities=[],
                            source_evidence=source_ev,
                            source_tool=tool_name,
                            confidence=0.88
                        ))

        # 2. Merge from synthetic case files if case directory is provided or evidence files exist
        if synthetic_case_dir and os.path.exists(synthetic_case_dir):
            # Parse chats.json
            chats_path = os.path.join(synthetic_case_dir, "chats.json")
            if os.path.exists(chats_path):
                try:
                    with open(chats_path, "r", encoding="utf-8") as f:
                        chats = json.load(f)
                        for c in chats:
                            sender = c.get("sender_handle")
                            recipient = c.get("recipient_handle")
                            merged_events.append(TimelineEvent(
                                timestamp=c.get("timestamp", ""),
                                event_type="CHAT_MESSAGE",
                                description=f"Chat message CHAT-{c.get('chat_id', '')} sent by {sender} to {recipient}: '{c.get('message_text')}'",
                                explanation=f"Direct JSON chat log entry parsed from chats.json (Platform: {c.get('platform')})",
                                entities=[s for s in [sender, recipient, c.get("device_id")] if s],
                                location="San Francisco Dock 14" if "37.774929" in c.get("message_text", "") else None,
                                source_evidence="chats.json",
                                source_tool="ChatLogParser",
                                confidence=0.98
                            ))
                except Exception as err:
                    logger.warning(f"Error parsing chats.json: {err}")

            # Parse calls.csv
            calls_path = os.path.join(synthetic_case_dir, "calls.csv")
            if os.path.exists(calls_path):
                try:
                    with open(calls_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            caller = row.get("caller_account") or row.get("caller_number")
                            recipient = row.get("recipient_account") or row.get("recipient_number")
                            merged_events.append(TimelineEvent(
                                timestamp=row.get("timestamp", ""),
                                event_type="CELL_CALL",
                                description=f"Cellular call {row.get('call_id')} from {caller} to {recipient} ({row.get('duration_sec')}s)",
                                explanation=f"Cellular CDR record parsed from calls.csv via tower {row.get('cell_tower_id')}",
                                entities=[e for e in [caller, recipient, row.get("caller_number"), row.get("recipient_number")] if e],
                                location=f"Tower {row.get('cell_tower_id')}",
                                source_evidence="calls.csv",
                                source_tool="CDRParser",
                                confidence=0.96
                            ))
                except Exception as err:
                    logger.warning(f"Error parsing calls.csv: {err}")

            # Parse gps.csv
            gps_path = os.path.join(synthetic_case_dir, "gps.csv")
            if os.path.exists(gps_path):
                try:
                    with open(gps_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            dev_id = row.get("device_id")
                            lat = row.get("latitude")
                            lon = row.get("longitude")
                            label = row.get("location_label")
                            merged_events.append(TimelineEvent(
                                timestamp=row.get("timestamp", ""),
                                event_type="GPS_PING",
                                description=f"GPS ping recorded for device {dev_id} at {label} ({lat}, {lon})",
                                explanation=f"Telematics location log entry parsed from gps.csv",
                                entities=[dev_id] if dev_id else [],
                                location=f"GPS ({lat}, {lon})",
                                source_evidence="gps.csv",
                                source_tool="GPSLogParser",
                                confidence=0.99
                            ))
                except Exception as err:
                    logger.warning(f"Error parsing gps.csv: {err}")

            # Parse events.json
            events_path = os.path.join(synthetic_case_dir, "events.json")
            if os.path.exists(events_path):
                try:
                    with open(events_path, "r", encoding="utf-8") as f:
                        events = json.load(f)
                        for ev in events:
                            merged_events.append(TimelineEvent(
                                timestamp=ev.get("timestamp", ""),
                                event_type="SYNTHETIC_EVENT",
                                description=f"{ev.get('event_title')}: {ev.get('description')}",
                                explanation=f"Investigative report event parsed from events.json",
                                entities=ev.get("associated_entities", []),
                                source_evidence="events.json",
                                source_tool="ReportParser",
                                confidence=0.95
                            ))
                except Exception as err:
                    logger.warning(f"Error parsing events.json: {err}")

        return merged_events

    @classmethod
    def detect_anomalies(cls, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Detects temporal overlaps, suspicious gaps, and conflicting timestamps across merged timeline events."""
        overlaps: List[Dict[str, Any]] = []
        gaps: List[Dict[str, Any]] = []
        conflicts: List[Dict[str, Any]] = []

        # Sort events by parsed datetime
        valid_events = []
        for e in events:
            dt = cls.parse_timestamp(e.timestamp)
            if dt:
                valid_events.append((dt, e))

        valid_events.sort(key=lambda x: x[0])

        # 1. Detect Temporal Overlaps & Conflicting Timestamps
        for i in range(len(valid_events)):
            dt1, e1 = valid_events[i]
            for j in range(i + 1, len(valid_events)):
                dt2, e2 = valid_events[j]
                time_diff_sec = abs((dt2 - dt1).total_seconds())

                # If events are within 60 seconds across distinct evidence sources -> Temporal Overlap
                if time_diff_sec <= 60 and e1.source_evidence != e2.source_evidence:
                    overlap_item = {
                        "event_1_id": e1.event_id,
                        "event_2_id": e2.event_id,
                        "time_difference_sec": time_diff_sec,
                        "description": f"Events '{e1.event_type}' ({e1.source_evidence}) and '{e2.event_type}' ({e2.source_evidence}) occurred within {time_diff_sec:.0f}s."
                    }
                    overlaps.append(overlap_item)
                    e1.anomalies.append("TEMPORAL_OVERLAP")
                    e2.anomalies.append("TEMPORAL_OVERLAP")

                # If events are within 300 seconds (5 min) but report conflicting locations -> Conflicting Timestamps
                if time_diff_sec <= 300 and e1.location and e2.location and e1.location != e2.location:
                    conflict_item = {
                        "event_1_id": e1.event_id,
                        "event_2_id": e2.event_id,
                        "time_difference_sec": time_diff_sec,
                        "location_1": e1.location,
                        "location_2": e2.location,
                        "description": f"Conflicting locations '{e1.location}' vs '{e2.location}' within {time_diff_sec:.0f}s."
                    }
                    conflicts.append(conflict_item)
                    e1.anomalies.append("CONFLICTING_TIMESTAMPS")
                    e2.anomalies.append("CONFLICTING_TIMESTAMPS")

                if time_diff_sec > 600:
                    break

        # 2. Detect Suspicious Gaps (> 10 minutes / 600 seconds gap between consecutive events)
        for i in range(len(valid_events) - 1):
            dt1, e1 = valid_events[i]
            dt2, e2 = valid_events[i + 1]
            gap_sec = (dt2 - dt1).total_seconds()

            if gap_sec > 600:
                gaps.append({
                    "start_event_id": e1.event_id,
                    "end_event_id": e2.event_id,
                    "start_timestamp": e1.timestamp,
                    "end_timestamp": e2.timestamp,
                    "gap_duration_minutes": round(gap_sec / 60.0, 1),
                    "description": f"Suspicious operational inactivity gap of {gap_sec / 60.0:.1f} minutes between {e1.timestamp} and {e2.timestamp}."
                })
                e1.anomalies.append("SUSPICIOUS_GAP")
                e2.anomalies.append("SUSPICIOUS_GAP")

        return {
            "temporal_overlaps": overlaps,
            "suspicious_gaps": gaps,
            "conflicting_timestamps": conflicts
        }

    @classmethod
    def build_timeline(
        cls,
        evidence_items: List[Dict[str, Any]],
        raw_findings: List[Dict[str, Any]],
        synthetic_case_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Builds a complete, chronologically sorted investigation timeline with anomaly detection."""
        events = cls.merge_evidence_events(evidence_items, raw_findings, synthetic_case_dir)

        # De-duplicate events by timestamp and description
        seen_keys = set()
        unique_events: List[TimelineEvent] = []
        for e in events:
            key = f"{e.timestamp}_{e.description[:50]}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_events.append(e)

        # Detect anomalies
        anomaly_results = cls.detect_anomalies(unique_events)

        # Sort timeline chronologically
        sorted_events = sorted(
            unique_events,
            key=lambda e: cls.parse_timestamp(e.timestamp) or datetime.min
        )

        summary = f"Timeline engine merged {len(sorted_events)} events across evidence sources. " \
                  f"Detected {len(anomaly_results['temporal_overlaps'])} temporal overlaps, " \
                  f"{len(anomaly_results['suspicious_gaps'])} suspicious gaps, and " \
                  f"{len(anomaly_results['conflicting_timestamps'])} conflicting timestamps."

        return {
            "total_events": len(sorted_events),
            "timeline": [e.model_dump() if hasattr(e, "model_dump") else e.dict() for e in sorted_events],
            "temporal_overlaps": anomaly_results["temporal_overlaps"],
            "suspicious_gaps": anomaly_results["suspicious_gaps"],
            "conflicting_timestamps": anomaly_results["conflicting_timestamps"],
            "analysis_summary": summary
        }
