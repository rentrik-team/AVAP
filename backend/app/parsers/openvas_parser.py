import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

from app.core.enums import ScannerType
from app.core.exceptions import ParserException
from app.parsers.base_parser import BaseParser
from app.parsers.models import AssessmentPackage, ParsedHost, ParsedService, ParsedVulnerability
from app.scanners.scan_artifact import ScanArtifact

logger = logging.getLogger(__name__)


class OpenVASParser(BaseParser):
    """Parser for OpenVAS (Greenbone) XML reports."""

    def _map_cvss_to_severity_rating(self, score: float) -> str:
        """Map a numeric CVSS score (0.0 - 10.0) to standard text rating."""
        if score <= 0.0:
            return "None"
        elif score < 4.0:
            return "Low"
        elif score < 7.0:
            return "Medium"
        elif score < 9.0:
            return "High"
        else:
            return "Critical"

    def _parse_port_protocol(self, port_str: Optional[str]) -> tuple[Optional[int], Optional[str]]:
        """Parse port/protocol string (e.g., '80/tcp', 'general/tcp', '123') into port and protocol.
        
        Returns:
            Tuple of (port, protocol)
        """
        if not port_str:
            return None, None

        port_str = port_str.strip().lower()
        if "/" in port_str:
            parts = port_str.split("/", 1)
            p_val, proto = parts[0], parts[1]
            try:
                return int(p_val), proto
            except ValueError:
                # E.g., "general/tcp" or "some_service/udp"
                return None, proto
        else:
            try:
                return int(port_str), "tcp"  # Default to tcp
            except ValueError:
                return None, None

    def parse(self, artifact: ScanArtifact) -> AssessmentPackage:
        """Parse OpenVAS XML output from the given artifact.
        
        Args:
            artifact: The ScanArtifact containing OpenVAS results.
            
        Returns:
            A populated AssessmentPackage.
        """
        if not artifact.output_path:
            raise ParserException("Scan artifact has no output path specified.")

        output_path = Path(artifact.output_path)
        if not output_path.exists():
            raise ParserException(f"OpenVAS output file not found at: {output_path}")

        logger.info(
            "Parsing OpenVAS XML output",
            extra={"scan_id": str(artifact.scan_id), "file_path": str(output_path)}
        )

        try:
            parser = ET.XMLParser(resolve_entities=False)
            tree = ET.parse(output_path, parser=parser)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(
                f"XML parse error in OpenVAS output: {e}",
                extra={"scan_id": str(artifact.scan_id), "file_path": str(output_path)}
            )
            raise ParserException(f"Failed to parse OpenVAS XML report: {e}") from e
        except Exception as e:
            logger.exception(
                f"Unexpected error reading OpenVAS output file: {e}",
                extra={"scan_id": str(artifact.scan_id)}
            )
            raise ParserException(f"Failed to read OpenVAS output file: {e}") from e

        # Fallback target defined at root level
        fallback_target = None
        target_node = root.find("target")
        if target_node is not None:
            fallback_target = target_node.text

        # Group vulnerabilities by Host -> Port/Protocol -> List of Vulnerabilities
        # Structure: Dict[host_ip, Dict[(port, protocol), List[ParsedVulnerability]]]
        grouped_data: Dict[str, Dict[tuple[Optional[int], Optional[str]], List[ParsedVulnerability]]] = {}

        # OpenVAS XML results can be under <results> directly (like in our stub)
        # or nested under <report><results> (real OpenVAS format).
        results_container = root.find("results")
        if results_container is None:
            report_node = root.find("report")
            if report_node is not None:
                results_container = report_node.find("results")

        if results_container is not None:
            for result_node in results_container.findall("result"):
                # Extract Host IP
                host_ip = None
                host_node = result_node.find("host")
                if host_node is not None:
                    host_ip = host_node.text
                
                # Fallback to general target if host node is empty
                if not host_ip:
                    host_ip = fallback_target

                if not host_ip:
                    continue  # Cannot parse result without host details

                # Clean host_ip string
                host_ip = host_ip.strip()

                # Extract Port/Protocol
                port_node = result_node.find("port")
                port_str = port_node.text if port_node is not None else None
                port_val, protocol = self._parse_port_protocol(port_str)

                # Extract Vulnerability Title
                name_node = result_node.find("name")
                v_name = name_node.text if name_node is not None else "Unknown Vulnerability"

                # Extract Severity Score
                severity_node = result_node.find("severity")
                severity_val = 0.0
                if severity_node is not None and severity_node.text:
                    try:
                        severity_val = float(severity_node.text)
                    except ValueError:
                        pass
                
                severity_rating = self._map_cvss_to_severity_rating(severity_val)

                # Extract Description
                desc_node = result_node.find("description")
                v_desc = desc_node.text if desc_node is not None else ""

                # Extract NVT details (CVE, refs)
                cve_val = None
                references = []
                nvt_node = result_node.find("nvt")
                if nvt_node is not None:
                    # NVT Name override if available
                    nvt_name_node = nvt_node.find("name")
                    if nvt_name_node is not None and nvt_name_node.text:
                        v_name = nvt_name_node.text

                    # CVE
                    cve_node = nvt_node.find("cve")
                    if cve_node is not None and cve_node.text and cve_node.text.lower() != "nocve":
                        cve_val = cve_node.text.strip()

                    # References
                    refs_node = nvt_node.find("refs")
                    if refs_node is not None:
                        for ref in refs_node.findall("ref"):
                            ref_id = ref.get("id")
                            if ref_id:
                                references.append(ref_id)

                # Construct parsed vulnerability object
                vuln = ParsedVulnerability(
                    name=v_name,
                    severity_score=severity_val,
                    severity_rating=severity_rating,
                    description=v_desc,
                    cve=cve_val,
                    port=port_val,
                    protocol=protocol,
                    references=references
                )

                # Map finding to Host -> Service
                if host_ip not in grouped_data:
                    grouped_data[host_ip] = {}
                
                service_key = (port_val, protocol)
                if service_key not in grouped_data[host_ip]:
                    grouped_data[host_ip][service_key] = []
                grouped_data[host_ip][service_key].append(vuln)

        # Build ParsedHost objects from grouped data
        parsed_hosts: List[ParsedHost] = []
        for host_ip, service_dict in grouped_data.items():
            parsed_services: List[ParsedService] = []
            for (port_val, protocol), vulns in service_dict.items():
                # We normalize "None" ports to port 0 (standard for general system-level findings)
                p_id = port_val if port_val is not None else 0
                proto = protocol if protocol is not None else "tcp"
                
                parsed_services.append(
                    ParsedService(
                        port=p_id,
                        protocol=proto,
                        service_name="general" if p_id == 0 else "unknown",
                        vulnerabilities=vulns
                    )
                )
            
            parsed_hosts.append(
                ParsedHost(
                    ipv4=host_ip,
                    services=parsed_services
                )
            )

        execution_metadata = {}
        # Parse version and execution info if available
        if root.get("id"):
            execution_metadata["report_id"] = root.get("id")

        return AssessmentPackage(
            scan_id=artifact.scan_id,
            scanner_type=ScannerType.OPENVAS,
            parsed_hosts=parsed_hosts,
            execution_metadata=execution_metadata
        )
