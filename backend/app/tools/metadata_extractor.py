import time
import os
from PIL import Image
from PIL.ExifTags import TAGS
import exifread
from typing import List, Dict, Any
from app.tools.registry import BaseInvestigativeTool, ToolInputSchema, ToolOutputSchema, StandardizedFinding, register_tool
from app.core.logging import logger

@register_tool()
class MetadataExtractor(BaseInvestigativeTool):
    name = "MetadataExtractor"
    description = "Extracts EXIF metadata, GPS coordinates, camera details, and creation timestamps from image files."
    supported_input_types = ["IMAGE", "FILE", "DOCUMENT"]
    capabilities = ["metadata_extraction", "exif", "gps_location", "device_identification"]

    async def execute(self, input_data: ToolInputSchema) -> ToolOutputSchema:
        start_time = time.time()
        file_path = input_data.file_path
        case_id = input_data.case_id
        evidence_id = input_data.evidence_id

        extracted_data: Dict[str, Any] = {
            "file_name": os.path.basename(file_path) if file_path else "unknown",
            "file_size_bytes": os.path.getsize(file_path) if (file_path and os.path.exists(file_path)) else 0,
            "exif_raw": {},
            "gps_coordinates": None,
            "device_model": None,
            "datetime_original": None
        }

        # Check synthetic exif overrides first
        if input_data.parameters and "synthetic_exif" in input_data.parameters:
            extracted_data.update(input_data.parameters["synthetic_exif"])
        elif file_path and os.path.exists(file_path):
            try:
                with Image.open(file_path) as img:
                    exif_data = img._getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag_name = TAGS.get(tag_id, str(tag_id))
                            if tag_name in ("Make", "Model"):
                                extracted_data["device_model"] = str(value)
                            elif tag_name in ("DateTimeOriginal", "DateTime"):
                                extracted_data["datetime_original"] = str(value)

                            if isinstance(value, (str, int, float)):
                                extracted_data["exif_raw"][tag_name] = value

                with open(file_path, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                    if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
                        lat_values = tags['GPS GPSLatitude'].values
                        lat_ref = str(tags.get('GPS GPSLatitudeRef', 'N'))
                        lon_values = tags['GPS GPSLongitude'].values
                        lon_ref = str(tags.get('GPS GPSLongitudeRef', 'E'))

                        lat_deg = float(lat_values[0].num) / float(lat_values[0].den)
                        lat_min = float(lat_values[1].num) / float(lat_values[1].den)
                        lat_sec = float(lat_values[2].num) / float(lat_values[2].den)

                        lon_deg = float(lon_values[0].num) / float(lon_values[0].den)
                        lon_min = float(lon_values[1].num) / float(lon_values[1].den)
                        lon_sec = float(lon_values[2].num) / float(lon_values[2].den)

                        lat = (lat_deg + lat_min/60.0 + lat_sec/3600.0) * (-1 if lat_ref == 'S' else 1)
                        lon = (lon_deg + lon_min/60.0 + lon_sec/3600.0) * (-1 if lon_ref == 'W' else 1)

                        extracted_data["gps_coordinates"] = {
                            "latitude": round(lat, 6),
                            "longitude": round(lon, 6)
                        }
            except Exception as e:
                logger.warning(f"Metadata extraction error on {file_path}: {e}")

        findings: List[StandardizedFinding] = []

        if extracted_data.get("gps_coordinates"):
            gps = extracted_data["gps_coordinates"]
            findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="GPS",
                entity_type="LOCATION",
                entity=f"{gps['latitude']},{gps['longitude']}",
                attribute="gps_coordinates",
                value=gps,
                confidence=0.98,
                source_tool=self.name,
                supporting_evidence={"file_name": extracted_data["file_name"]}
            ))

        if extracted_data.get("device_model"):
            dev = extracted_data["device_model"]
            findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="METADATA",
                entity_type="DEVICE",
                entity=dev,
                attribute="device_model",
                value=dev,
                confidence=0.95,
                source_tool=self.name,
                supporting_evidence={"file_name": extracted_data["file_name"]}
            ))

        if extracted_data.get("datetime_original"):
            dt = extracted_data["datetime_original"]
            findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="METADATA",
                entity_type="DATETIME",
                entity=str(dt),
                attribute="datetime_original",
                value=str(dt),
                confidence=0.95,
                source_tool=self.name,
                supporting_evidence={"file_name": extracted_data["file_name"]}
            ))

        return ToolOutputSchema(
            tool_name=self.name,
            success=True,
            findings_extracted=len(findings),
            data=extracted_data,
            findings=findings,
            execution_time_ms=(time.time() - start_time) * 1000
        )

# Backward compatibility alias
ExifMetadataExtractorTool = MetadataExtractor
