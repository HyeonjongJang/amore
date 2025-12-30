"""
CRM Message Generation System - Main Entry Point
Multi-Agent workflow using LangGraph
"""
import json
from typing import Dict, Any, Optional, TypedDict, Annotated, Union
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from langgraph.graph import StateGraph, END

# Import agents
from agents.persona_analyzer import PersonaAnalyzerAgent
from agents.product_matcher import ProductMatcherAgent
from agents.message_generator import MessageGeneratorAgent
from agents.quality_checker import QualityCheckerAgent

# Import data loaders
from config import PERSONAS_PATH, BRAND_TONES_PATH, CRM_EXAMPLES_PATH


# Define the state schema
class CRMState(TypedDict):
    """State for CRM message generation workflow"""
    # Input
    persona: Dict[str, Any]
    campaign_purpose: str
    brand: str
    season_event: str

    # Intermediate results
    persona_analysis: Dict[str, Any]
    product_match: Dict[str, Any]
    generated_messages: Dict[str, Any]
    quality_report: Dict[str, Any]

    # Output
    final_output: Dict[str, Any]

    # Metadata
    error: Optional[str]
    retry_count: int


class CRMMessageGenerator:
    """Main CRM Message Generation System with Multi-Agent Workflow"""

    def __init__(self):
        self.personas = self._load_personas()
        self.brand_tones = self._load_brand_tones()
        self.crm_examples = self._load_crm_examples()

        # Initialize agents
        self.persona_analyzer = PersonaAnalyzerAgent()
        self.product_matcher = ProductMatcherAgent()
        self.message_generator = MessageGeneratorAgent(brand_tones=self.brand_tones)
        self.quality_checker = QualityCheckerAgent(brand_tones=self.brand_tones)

        # Build workflow
        self.workflow = self._build_workflow()

    def _load_personas(self) -> Dict[str, Dict]:
        """Load personas from JSON file"""
        try:
            with open(PERSONAS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Create lookup by ID and name
            personas = {}
            for p in data.get('personas', []):
                personas[p['id']] = p
                personas[p['name']] = p
            return personas
        except FileNotFoundError:
            return {}

    def _load_brand_tones(self) -> Dict[str, Dict]:
        """Load brand tones from JSON file"""
        try:
            with open(BRAND_TONES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('brands', {})
        except FileNotFoundError:
            return {}

    def _load_crm_examples(self) -> str:
        """Load CRM examples for reference"""
        try:
            with open(CRM_EXAMPLES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Format examples as text
            examples = []
            for ex in data.get('examples', [])[:3]:  # Top 3 examples
                examples.append(
                    f"[{ex['brand']}] 타겟: {ex['target_persona']}\n"
                    f"제목: {ex['title']}\n"
                    f"본문: {ex['body'][:100]}...\n"
                    f"CTR: {ex['ctr']}%"
                )
            return "\n\n".join(examples)
        except FileNotFoundError:
            return ""

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(CRMState)

        # Add nodes
        workflow.add_node("analyze_persona", self._analyze_persona_node)
        workflow.add_node("match_products", self._match_products_node)
        workflow.add_node("generate_messages", self._generate_messages_node)
        workflow.add_node("check_quality", self._check_quality_node)
        workflow.add_node("prepare_output", self._prepare_output_node)

        # Define edges
        workflow.set_entry_point("analyze_persona")
        workflow.add_edge("analyze_persona", "match_products")
        workflow.add_edge("match_products", "generate_messages")
        workflow.add_edge("generate_messages", "check_quality")

        # Conditional edge based on quality check
        workflow.add_conditional_edges(
            "check_quality",
            self._should_retry,
            {
                "retry": "generate_messages",
                "accept": "prepare_output"
            }
        )

        workflow.add_edge("prepare_output", END)

        return workflow.compile()

    def _analyze_persona_node(self, state: CRMState) -> Dict[str, Any]:
        """Node: Analyze persona"""
        try:
            analysis = self.persona_analyzer.analyze(
                persona=state['persona'],
                campaign_purpose=state['campaign_purpose'],
                brand=state['brand'],
                season_event=state['season_event']
            )
            return {"persona_analysis": analysis}
        except Exception as e:
            return {"error": f"Persona analysis failed: {str(e)}"}

    def _match_products_node(self, state: CRMState) -> Dict[str, Any]:
        """Node: Match products using RAG"""
        try:
            match = self.product_matcher.match_products(
                persona=state['persona'],
                persona_analysis=state['persona_analysis'],
                campaign_purpose=state['campaign_purpose'],
                brand=state['brand'],
                season_event=state['season_event']
            )
            # Debug logging
            print(f"[DEBUG] Product match result: {len(match.get('selected_products', []))} products")
            print(f"[DEBUG] Total retrieved: {match.get('total_retrieved', 0)}")
            return {"product_match": match}
        except Exception as e:
            print(f"[DEBUG] Product matching error: {str(e)}")
            return {"error": f"Product matching failed: {str(e)}"}

    def _generate_messages_node(self, state: CRMState) -> Dict[str, Any]:
        """Node: Generate CRM messages"""
        try:
            # Get relevant CRM examples for the brand
            crm_examples = self._get_relevant_examples(
                state['brand'],
                state['persona'].get('name', '')
            )

            messages = self.message_generator.generate(
                persona=state['persona'],
                persona_analysis=state['persona_analysis'],
                product_match=state['product_match'],
                brand=state['brand'],
                campaign_purpose=state['campaign_purpose'],
                season_event=state['season_event'],
                crm_examples=crm_examples
            )
            return {"generated_messages": messages}
        except Exception as e:
            return {"error": f"Message generation failed: {str(e)}"}

    def _check_quality_node(self, state: CRMState) -> Dict[str, Any]:
        """Node: Check message quality"""
        try:
            report = self.quality_checker.validate(
                generated_message=state['generated_messages'],
                persona=state['persona'],
                brand=state['brand'],
                campaign_purpose=state['campaign_purpose'],
                season_event=state['season_event']
            )

            # Increment retry count
            retry_count = state.get('retry_count', 0) + 1

            return {
                "quality_report": report,
                "retry_count": retry_count
            }
        except Exception as e:
            return {"error": f"Quality check failed: {str(e)}"}

    def _should_retry(self, state: CRMState) -> str:
        """Decide whether to retry message generation"""
        quality = state.get('quality_report', {})
        retry_count = state.get('retry_count', 0)

        # Check if we should retry
        verdict = quality.get('final_verdict', 'APPROVED')
        actual_counts = quality.get('actual_counts', {})

        # Don't retry more than 2 times
        if retry_count >= 2:
            return "accept"

        # Retry if character limits not met or rejected
        if verdict == 'REJECTED':
            return "retry"

        if not actual_counts.get('title_passed', True) or not actual_counts.get('body_passed', True):
            return "retry"

        return "accept"

    def _prepare_output_node(self, state: CRMState) -> Dict[str, Any]:
        """Node: Prepare final output"""
        # Get quality summary
        quality_summary = self.quality_checker.get_summary_score(
            state.get('quality_report', {})
        )

        final_output = {
            "persona": {
                "id": state['persona'].get('id'),
                "name": state['persona'].get('name')
            },
            "brand": state['brand'],
            "campaign_purpose": state['campaign_purpose'],
            "season_event": state['season_event'],
            "messages": state.get('generated_messages', {}),
            "quality_summary": quality_summary,
            "quality_details": state.get('quality_report', {}),
            "recommended_products": state.get('product_match', {}).get('selected_products', []),
            "persona_insights": state.get('persona_analysis', {}),
            "retry_count": state.get('retry_count', 0)
        }

        return {"final_output": final_output}

    def _get_relevant_examples(self, brand: str, persona_type: str) -> str:
        """Get relevant CRM examples for the brand/persona"""
        try:
            with open(CRM_EXAMPLES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Find relevant examples
            relevant = []
            for ex in data.get('examples', []):
                if ex['brand'] == brand or persona_type in ex['target_persona']:
                    relevant.append(
                        f"제목: {ex['title']}\n본문: {ex['body'][:150]}..."
                    )
                    if len(relevant) >= 2:
                        break

            return "\n\n".join(relevant) if relevant else ""
        except:
            return ""

    def get_persona(self, persona_id_or_name: str) -> Optional[Dict]:
        """Get persona by ID or name"""
        return self.personas.get(persona_id_or_name)

    def list_personas(self) -> list:
        """List all available personas"""
        seen = set()
        personas = []
        for key, p in self.personas.items():
            if p['id'] not in seen:
                personas.append({
                    'id': p['id'],
                    'name': p['name'],
                    'age_group': p['age_group'],
                    'skin_type': p['skin_type']
                })
                seen.add(p['id'])
        return personas

    def list_brands(self) -> list:
        """List all available brands"""
        return list(self.brand_tones.keys())

    def generate(
        self,
        persona_id_or_name: Union[str, Dict[str, Any]],
        brand: str,
        campaign_purpose: str,
        season_event: str = "일반"
    ) -> Dict[str, Any]:
        """
        Generate CRM message for a persona

        Args:
            persona_id_or_name: Persona ID (e.g., "P001"), name (e.g., "트렌드세터 지영"),
                               or a complete persona dictionary (for custom personas)
            brand: Brand name (Korean, e.g., "헤라")
            campaign_purpose: Campaign purpose
            season_event: Season or event context

        Returns:
            Final output containing messages, quality report, etc.
        """
        # Get persona - handle both string lookup and direct persona dict
        if isinstance(persona_id_or_name, dict):
            # Direct persona dictionary (custom persona)
            persona = persona_id_or_name
        else:
            # Lookup by ID or name
            persona = self.get_persona(persona_id_or_name)
            if not persona:
                return {"error": f"Persona not found: {persona_id_or_name}"}

        # Initialize state
        initial_state: CRMState = {
            "persona": persona,
            "campaign_purpose": campaign_purpose,
            "brand": brand,
            "season_event": season_event,
            "persona_analysis": {},
            "product_match": {},
            "generated_messages": {},
            "quality_report": {},
            "final_output": {},
            "error": None,
            "retry_count": 0
        }

        # Run workflow
        result = self.workflow.invoke(initial_state)

        # Check for errors
        if result.get('error'):
            return {"error": result['error']}

        return result.get('final_output', {})


# Convenience function
def run_crm_agent(
    persona_id: str,
    brand: str,
    campaign_purpose: str,
    season_event: str = "일반"
) -> Dict[str, Any]:
    """
    Run the CRM message generation agent

    Args:
        persona_id: Persona ID or name
        brand: Brand name
        campaign_purpose: Campaign purpose
        season_event: Season/event context

    Returns:
        Generated CRM messages and analysis
    """
    generator = CRMMessageGenerator()
    return generator.generate(
        persona_id_or_name=persona_id,
        brand=brand,
        campaign_purpose=campaign_purpose,
        season_event=season_event
    )


# Test function
def test_full_pipeline():
    """Test the complete pipeline"""
    print("=" * 70)
    print("CRM MESSAGE GENERATION SYSTEM - FULL PIPELINE TEST")
    print("=" * 70)

    generator = CRMMessageGenerator()

    # List available personas and brands
    print("\nAvailable Personas:")
    for p in generator.list_personas():
        print(f"  • {p['id']}: {p['name']} ({p['age_group']}, {p['skin_type']})")

    print("\nAvailable Brands:")
    print(f"  {', '.join(generator.list_brands())}")

    # Test with first persona
    print("\n" + "-" * 70)
    print("Running test generation...")
    print("-" * 70)

    result = generator.generate(
        persona_id_or_name="P001",  # 트렌드세터 지영
        brand="헤라",
        campaign_purpose="신제품 런칭",
        season_event="봄 신상"
    )

    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return result

    # Print results
    print("\n" + "=" * 70)
    print("GENERATION RESULTS")
    print("=" * 70)

    print(f"\nPersona: {result['persona']['name']}")
    print(f"Brand: {result['brand']}")
    print(f"Campaign: {result['campaign_purpose']}")
    print(f"Retries: {result['retry_count']}")

    # Main message
    if 'messages' in result and 'main_message' in result['messages']:
        msg = result['messages']['main_message']
        print("\n--- MAIN MESSAGE ---")
        print(f"제목 ({len(msg.get('title', ''))}자): {msg.get('title', '')}")
        print(f"\n본문 ({len(msg.get('body', ''))}자):")
        print(msg.get('body', ''))
        print(f"\nCTA: {msg.get('cta', '')}")

    # Quality summary
    if 'quality_summary' in result:
        qs = result['quality_summary']
        print("\n--- QUALITY SUMMARY ---")
        print(f"Average Score: {qs.get('average_score', 0)}/10")
        print(f"Verdict: {qs.get('verdict', 'N/A')}")
        print(f"Char Limits Passed: {qs.get('char_limits_passed', False)}")

    # Recommended products
    if result.get('recommended_products'):
        print("\n--- RECOMMENDED PRODUCTS ---")
        for p in result['recommended_products'][:2]:
            print(f"  • {p.get('product_name', 'N/A')} - {p.get('brand', 'N/A')}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE!")
    print("=" * 70)

    return result


if __name__ == "__main__":
    test_full_pipeline()
