#!/usr/bin/env python3
"""
Data Quality Audit Script for HappyCow Scraper
==============================================

Analyzes scraped restaurant data for completeness, accuracy, and quality issues.
Provides detailed reports and statistics on extraction success rates.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import random

from config import ScraperConfig
from supabase import create_client, Client
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich import print as rprint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FieldAuditResult:
    """Results for a single field audit"""
    field_name: str
    total_records: int
    populated_count: int
    empty_count: int
    null_count: int
    completeness_rate: float
    sample_values: List[str]
    
    def __post_init__(self):
        self.completeness_rate = (self.populated_count / self.total_records) * 100 if self.total_records > 0 else 0

@dataclass
class AuditReport:
    """Complete audit report"""
    total_restaurants: int
    audit_timestamp: datetime
    recent_records_count: int
    field_results: List[FieldAuditResult]
    data_quality_issues: List[str]
    recommendations: List[str]

class RestaurantAuditor:
    """Audits restaurant data quality and extraction accuracy"""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.supabase: Client = create_client(config.supabase_url, config.supabase_key)
        self.console = Console()
        
        # Critical fields that should be populated
        self.critical_fields = [
            'name', 'city', 'happycow_url', 'vegan_status'
        ]
        
        # Important fields that should be mostly populated
        self.important_fields = [
            'address', 'description', 'phone', 'website', 'rating'
        ]
        
        # Optional fields
        self.optional_fields = [
            'cuisine_types', 'hours', 'features', 'latitude', 'longitude',
            'instagram', 'facebook', 'price_range', 'review_count'
        ]
    
    async def get_recent_restaurants(self, days: int = 7) -> List[Dict]:
        """Get restaurants added in the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            result = self.supabase.table('restaurants').select('*').gte(
                'created_at', cutoff_date.isoformat()
            ).execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error fetching recent restaurants: {e}")
            return []
    
    async def get_sample_restaurants(self, sample_size: int = 100) -> List[Dict]:
        """Get a random sample of restaurants for audit"""
        try:
            # Get total count first
            count_result = self.supabase.table('restaurants').select('id', count='exact').execute()
            total_count = count_result.count
            
            if total_count <= sample_size:
                # Get all if sample size is larger than total
                result = self.supabase.table('restaurants').select('*').execute()
                return result.data
            else:
                # Get random sample by selecting random offset
                offset = random.randint(0, max(0, total_count - sample_size))
                result = self.supabase.table('restaurants').select('*').range(
                    offset, offset + sample_size - 1
                ).execute()
                return result.data
                
        except Exception as e:
            logger.error(f"Error fetching sample restaurants: {e}")
            return []
    
    def audit_field(self, restaurants: List[Dict], field_name: str) -> FieldAuditResult:
        """Audit a specific field across all restaurants"""
        total_records = len(restaurants)
        populated_count = 0
        empty_count = 0
        null_count = 0
        sample_values = []
        
        for restaurant in restaurants:
            value = restaurant.get(field_name)
            
            if value is None:
                null_count += 1
            elif isinstance(value, str) and value.strip() == '':
                empty_count += 1
            elif isinstance(value, list) and len(value) == 0:
                empty_count += 1
            elif isinstance(value, dict) and len(value) == 0:
                empty_count += 1
            else:
                populated_count += 1
                # Collect sample values
                if len(sample_values) < 5:
                    if isinstance(value, (list, dict)):
                        sample_values.append(str(value)[:100] + '...' if len(str(value)) > 100 else str(value))
                    else:
                        sample_values.append(str(value)[:100] + '...' if len(str(value)) > 100 else str(value))
        
        return FieldAuditResult(
            field_name=field_name,
            total_records=total_records,
            populated_count=populated_count,
            empty_count=empty_count,
            null_count=null_count,
            completeness_rate=0.0,  # Will be calculated in __post_init__
            sample_values=sample_values
        )
    
    def identify_data_quality_issues(self, field_results: List[FieldAuditResult]) -> List[str]:
        """Identify potential data quality issues"""
        issues = []
        
        # Check critical fields
        for result in field_results:
            if result.field_name in self.critical_fields:
                if result.completeness_rate < 95:
                    issues.append(f"Critical field '{result.field_name}' has low completeness: {result.completeness_rate:.1f}%")
            
            elif result.field_name in self.important_fields:
                if result.completeness_rate < 70:
                    issues.append(f"Important field '{result.field_name}' has low completeness: {result.completeness_rate:.1f}%")
        
        # Check for specific patterns
        name_result = next((r for r in field_results if r.field_name == 'name'), None)
        if name_result and name_result.populated_count < name_result.total_records * 0.98:
            issues.append("Some restaurants missing names - extraction may be failing")
        
        address_result = next((r for r in field_results if r.field_name == 'address'), None)
        if address_result and address_result.completeness_rate < 50:
            issues.append("Low address completion - location extraction needs improvement")
        
        coords_lat = next((r for r in field_results if r.field_name == 'latitude'), None)
        coords_lng = next((r for r in field_results if r.field_name == 'longitude'), None)
        if coords_lat and coords_lng:
            if abs(coords_lat.completeness_rate - coords_lng.completeness_rate) > 5:
                issues.append("Latitude/longitude completion rates differ - coordinate extraction inconsistent")
        
        return issues
    
    def generate_recommendations(self, field_results: List[FieldAuditResult], issues: List[str]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if any("Critical field" in issue for issue in issues):
            recommendations.append("Review and improve LLM extraction prompts for critical fields")
        
        if any("address" in issue.lower() for issue in issues):
            recommendations.append("Enhance address extraction - check for multiple address formats")
        
        if any("coordinate" in issue.lower() for issue in issues):
            recommendations.append("Improve coordinate extraction from map embeds and links")
        
        rating_result = next((r for r in field_results if r.field_name == 'rating'), None)
        if rating_result and rating_result.completeness_rate < 40:
            recommendations.append("Review rating extraction - may need different selectors")
        
        hours_result = next((r for r in field_results if r.field_name == 'hours'), None)
        if hours_result and hours_result.completeness_rate < 30:
            recommendations.append("Hours extraction needs improvement - check for collapsed sections")
        
        # General recommendations
        if len(issues) > 3:
            recommendations.append("Consider using GPT-4 for more accurate extraction")
            recommendations.append("Add extraction confidence scoring and retry logic")
        
        return recommendations
    
    async def run_audit(self, sample_size: int = 100, recent_days: int = 7) -> AuditReport:
        """Run complete audit and generate report"""
        
        rprint("[bold blue]🔍 Starting Restaurant Data Audit[/bold blue]")
        
        # Get data
        with Progress() as progress:
            task = progress.add_task("Fetching restaurant data...", total=2)
            
            # Get sample for comprehensive audit
            sample_restaurants = await self.get_sample_restaurants(sample_size)
            progress.update(task, advance=1)
            
            # Get recent restaurants for trend analysis
            recent_restaurants = await self.get_recent_restaurants(recent_days)
            progress.update(task, advance=1)
        
        if not sample_restaurants:
            rprint("[red]❌ No restaurant data found for audit[/red]")
            return AuditReport(
                total_restaurants=0,
                audit_timestamp=datetime.now(),
                recent_records_count=0,
                field_results=[],
                data_quality_issues=["No data available for audit"],
                recommendations=["Check database connection and data availability"]
            )
        
        rprint(f"[green]📊 Auditing {len(sample_restaurants)} restaurants ({len(recent_restaurants)} recent)[/green]")
        
        # Audit all fields
        all_fields = self.critical_fields + self.important_fields + self.optional_fields
        field_results = []
        
        with Progress() as progress:
            task = progress.add_task("Auditing fields...", total=len(all_fields))
            
            for field in all_fields:
                result = self.audit_field(sample_restaurants, field)
                field_results.append(result)
                progress.update(task, advance=1)
        
        # Identify issues and generate recommendations
        issues = self.identify_data_quality_issues(field_results)
        recommendations = self.generate_recommendations(field_results, issues)
        
        return AuditReport(
            total_restaurants=len(sample_restaurants),
            audit_timestamp=datetime.now(),
            recent_records_count=len(recent_restaurants),
            field_results=field_results,
            data_quality_issues=issues,
            recommendations=recommendations
        )
    
    def print_report(self, report: AuditReport):
        """Print formatted audit report"""
        
        # Header
        self.console.print("\n" + "="*80)
        self.console.print(f"[bold]🍽️  RESTAURANT DATA AUDIT REPORT[/bold]")
        self.console.print("="*80)
        self.console.print(f"Audit Time: {report.audit_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        self.console.print(f"Sample Size: {report.total_restaurants} restaurants")
        self.console.print(f"Recent Records: {report.recent_records_count} (last 7 days)")
        
        # Field completeness table
        self.console.print("\n[bold]📋 Field Completeness Analysis[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Field", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Populated", justify="right")
        table.add_column("Empty", justify="right")
        table.add_column("Null", justify="right")
        table.add_column("Rate", justify="right")
        table.add_column("Sample Values", style="dim")
        
        for result in report.field_results:
            # Determine field type
            field_type = "🔴 Critical" if result.field_name in self.critical_fields else \
                        "🟡 Important" if result.field_name in self.important_fields else \
                        "🟢 Optional"
            
            # Color code completion rate
            rate_color = "green" if result.completeness_rate >= 80 else \
                        "yellow" if result.completeness_rate >= 50 else "red"
            
            sample_text = "; ".join(result.sample_values[:2]) if result.sample_values else "N/A"
            
            table.add_row(
                result.field_name,
                field_type,
                str(result.populated_count),
                str(result.empty_count),
                str(result.null_count),
                f"[{rate_color}]{result.completeness_rate:.1f}%[/{rate_color}]",
                sample_text
            )
        
        self.console.print(table)
        
        # Data quality issues
        if report.data_quality_issues:
            self.console.print("\n[bold red]⚠️  Data Quality Issues[/bold red]")
            for issue in report.data_quality_issues:
                self.console.print(f"  • {issue}")
        else:
            self.console.print("\n[bold green]✅ No major data quality issues detected[/bold green]")
        
        # Recommendations
        if report.recommendations:
            self.console.print("\n[bold blue]💡 Recommendations[/bold blue]")
            for rec in report.recommendations:
                self.console.print(f"  • {rec}")
        
        # Summary
        critical_results = [r for r in report.field_results if r.field_name in self.critical_fields]
        important_results = [r for r in report.field_results if r.field_name in self.important_fields]
        
        critical_avg = sum(r.completeness_rate for r in critical_results) / len(critical_results) if critical_results else 0
        important_avg = sum(r.completeness_rate for r in important_results) / len(important_results) if important_results else 0
        
        self.console.print("\n[bold]📈 Summary[/bold]")
        self.console.print(f"Critical Fields Average: {critical_avg:.1f}%")
        self.console.print(f"Important Fields Average: {important_avg:.1f}%")
        self.console.print(f"Overall Data Quality: {'Good' if critical_avg >= 90 and important_avg >= 70 else 'Needs Improvement'}")
        
        self.console.print("\n" + "="*80)
    
    async def save_report(self, report: AuditReport, filename: str = None):
        """Save audit report to JSON file"""
        if not filename:
            timestamp = report.audit_timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"audit_report_{timestamp}.json"
        
        report_dict = asdict(report)
        # Convert datetime to string for JSON serialization
        report_dict['audit_timestamp'] = report.audit_timestamp.isoformat()
        
        with open(filename, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        rprint(f"[green]💾 Report saved to {filename}[/green]")

async def main():
    """Main audit execution"""
    try:
        config = ScraperConfig.from_env()
        auditor = RestaurantAuditor(config)
        
        # Run audit
        report = await auditor.run_audit(sample_size=100)
        
        # Print report
        auditor.print_report(report)
        
        # Save report
        await auditor.save_report(report)
        
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main())) 