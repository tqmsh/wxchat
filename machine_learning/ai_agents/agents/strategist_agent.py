"""
Strategist Agent - LangChain Implementation

Generates draft solutions with Chain-of-Thought reasoning using LangChain.
"""

import time
import uuid
import json
import re
from typing import List, Dict, Any
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain, TransformChain, SequentialChain
from langchain.output_parsers import PydanticOutputParser
# Messages handled via tuple format in ChatPromptTemplate
from pydantic import BaseModel, Field

from ai_agents.state import WorkflowState, DraftContent, ChainOfThought, log_agent_execution
from ai_agents.utils import create_langchain_llm

# Import simple logger for backup logging
try:
    from ai_agents.simple_logger import simple_log
except:
    class SimpleLogFallback:
        def info(self, msg, data=None): pass
        def error(self, msg, data=None): pass
    simple_log = SimpleLogFallback()


class ChainOfThoughtStep(BaseModel):
    """Pydantic model for CoT step parsing"""
    step: int = Field(description="Step number")
    thought: str = Field(description="The reasoning for this step")
    confidence: float = Field(description="Confidence score 0-1")


class DraftOutput(BaseModel):
    """Pydantic model for draft output parsing"""
    draft_content: str = Field(description="The complete draft solution")
    chain_of_thought: List[ChainOfThoughtStep] = Field(description="Step-by-step reasoning")


class StrategistAgent:
    """
    Strategy Proposer using LangChain chains.
    
    Generates well-structured draft solutions with explicit Chain-of-Thought reasoning.
    Designed to be creative and explore multiple solution paths.
    """
    
    def __init__(self, context):
        self.context = context
        self.logger = context.logger.getChild("strategist")
        self.llm_client = context.llm_client
        self.llm = create_langchain_llm(self.llm_client)
        
        # Setup chains
        self._setup_chains()
        
    def _setup_chains(self):
        """Setup CHAINED LangChain workflow for draft generation"""
        
        # Parser for structured output
        self.output_parser = PydanticOutputParser(pydantic_object=DraftOutput)
        
        # NEW: Context Analysis Chain (Step 1)
        # Analyzes the context to identify key information
        self.context_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """Analyze the retrieved course content to identify specific lesson information."""),
                ("human", """Query: {query}

Retrieved Course Content:
{context}

Carefully analyze the retrieved context and extract:
1. SPECIFIC LESSON TOPICS covered (e.g., "Branch Prediction", "Cache Design", "RISC-V Processor Design")  
2. KEY TECHNICAL CONCEPTS with details (algorithms, formulas, architectures)
3. CONCRETE EXAMPLES and code snippets present in the context
4. DIAGRAMS or visual content described
5. Overall lesson focus and learning objectives

Output as JSON:
{{
    "key_topics": ["List specific topics from the context"],
    "technical_concepts": ["List specific algorithms, formulas, or technical details"],
    "examples_present": ["List concrete examples found in context"], 
    "lesson_focus": "What the main lesson was about based on context",
    "context_quality": "high/medium/low",
    "suggested_approach": "How to organize this content to answer the query"
}}""")
            ]),
            output_key="context_insights"
        )
        
        # Main draft generation chain (Step 2)
        # NOW USES context insights from Step 1!
        self.draft_generation_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are an expert problem solver and educator specializing in computer science and engineering.

CRITICAL INSTRUCTIONS:
1. You MUST answer based ONLY on the retrieved context provided below
2. The context contains actual course materials - use EXACTLY what is in those retrieved documents
3. DO NOT use your general knowledge about Newton's laws, physics, or any other topics
4. DO NOT make up content that is not in the retrieved context
5. If the query asks about "yesterday's lesson", summarize the topics that appear in the retrieved context
6. Read the retrieved context carefully and base your entire answer on what you actually find there

IMPORTANT: The retrieved context below contains the actual lesson content. Use it!

{course_prompt}"""),
                ("human", """Query: {query}

RETRIEVED CONTEXT FROM COURSE MATERIALS:
{context}

CONTEXT ANALYSIS INSIGHTS:
{context_insights}

Previous feedback (if any): {feedback}

MANDATORY INSTRUCTIONS:
The context above contains actual course materials about computer science topics like Cache Design, RISC-V Processor Design, Performance Analysis, etc.

You MUST:
1. Read the retrieved context carefully - it contains lesson content about computer architecture
2. Identify the specific topics covered (like Cache Design, Processor Architecture, etc.)
3. Answer the query using ONLY these topics from the retrieved context
4. DO NOT mention Newton's laws, physics, or any content not in the retrieved context

EXAMPLE: If the context contains "Cache Design - 3C model of cache misses", then discuss cache design topics, NOT physics.

Your response MUST be valid JSON using ONLY the retrieved context above:
{{
    "draft_content": "<Summarize the actual lesson topics from the retrieved context - like Cache Design, RISC-V Architecture, Performance, etc. Do NOT mention topics not in the context>",
    "chain_of_thought": [
        {{
            "step": 1,
            "thought": "<List the specific topics you found in the retrieved context (Cache Design, Processor Design, etc.)>",
            "confidence": 0.9
        }},
        {{
            "step": 2, 
            "thought": "<Explain how these topics from the context answer the lesson query>",
            "confidence": 0.9
        }}
    ]
}}

CRITICAL: Answer using the computer science topics in the context, NOT physics or other subjects.""")
            ]),
            output_key="draft_output"
        )
        
        # NEW: Self-Assessment Chain (Step 3)
        # The draft assesses its own quality!
        self.self_assessment_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """Assess the quality of the generated draft."""),
                ("human", """Query: {query}

Context Insights:
{context_insights}

Generated Draft:
{draft_output}

Assess the draft quality:
1. Does it answer the query completely?
2. Does it use the context effectively?
3. Is the reasoning clear and logical?
4. What could be improved?

Output as JSON:
{{
    "completeness_score": <0.0-1.0>,
    "context_usage_score": <0.0-1.0>,
    "clarity_score": <0.0-1.0>,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "overall_quality": "high/medium/low"
}}""")
            ]),
            output_key="quality_assessment"
        )
        
        # CREATE THE SEQUENTIAL CHAIN - Connect all three steps!
        self.draft_pipeline = SequentialChain(
            chains=[
                self.context_analysis_chain,
                self.draft_generation_chain,
                self.self_assessment_chain
            ],
            input_variables=["query", "context", "feedback", "course_prompt"],
            output_variables=["draft_output", "quality_assessment"],
            verbose=True  # See the chain in action!
        )
        
        # Chain for iterative refinement
        self.refinement_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are refining a draft solution based on feedback.
                Address the specific issues while maintaining the good parts.
                DO NOT use template placeholders."""),
                ("human", """Original Query: {query}

Previous Draft:
{previous_draft}

Feedback to address:
{feedback}

Context:
{context}

Based on the feedback and context, generate an IMPROVED solution.

IMPORTANT: Write the ACTUAL improved content, not placeholders.

Your response MUST be valid JSON:
{{
    "draft_content": "<Your actual improved solution here>",
    "chain_of_thought": [
        {{
            "step": 1,
            "thought": "<Your actual reasoning>",
            "confidence": 0.9
        }}
    ]
}}""")
            ])
        )
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Generate draft solution with Chain-of-Thought"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(f"STRATEGIST AGENT - ROUND {state['current_round'] + 1}")
            simple_log.info(f"STRATEGIST AGENT - ROUND {state['current_round'] + 1}")
            self.logger.info("="*250)
            simple_log.info("="*250)
            simple_log.info("STRATEGIST START", {
                "round": state['current_round'] + 1,
                "query": state['query'][:50]
            })
            
            query = state["query"]
            context = state["retrieval_results"]
            feedback = state.get("moderator_feedback")
            course_prompt = state.get("course_prompt", "")
            
            # Increment round counter
            state["current_round"] += 1
            
            # Debug logging to see what we're getting
            self.logger.info(f"DEBUG: Retrieved context type: {type(context)}")
            simple_log.info(f"DEBUG: Retrieved context type: {type(context)}")
            self.logger.info(f"DEBUG: Retrieved context length: {len(context) if context else 0}")
            simple_log.info(f"DEBUG: Retrieved context length: {len(context) if context else 0}")
            simple_log.info("STRATEGIST CONTEXT", {
                "context_type": str(type(context)),
                "context_length": len(context) if context else 0
            })
            if context and len(context) > 0:
                self.logger.info(f"DEBUG: First context item keys: {context[0].keys() if isinstance(context[0], dict) else 'Not a dict'}")
                simple_log.info(f"DEBUG: First context item keys: {context[0].keys() if isinstance(context[0], dict) else 'Not a dict'}")
            
            # Prepare context string
            context_str = self._format_context(context)
            self.logger.info(f"DEBUG: Formatted context length: {len(context_str)} chars")
            simple_log.info(f"DEBUG: Formatted context length: {len(context_str)} chars")
            self.logger.info(f"DEBUG: Context: {context_str}" if context_str else "DEBUG: Empty context!")
            simple_log.info(f"DEBUG: Context: {context_str}" if context_str else "DEBUG: Empty context!")
            
            # Choose chain based on whether we have feedback
            if feedback and state.get("draft"):
                self.logger.info("Refining previous draft based on feedback")
                simple_log.info("Refining previous draft based on feedback")
                self.logger.info(f"Feedback: {feedback}")
                simple_log.info(f"Feedback: {feedback}")
                
                # Use refinement chain
                self.logger.info("="*250)
                simple_log.info("="*250)
                self.logger.info("LLM INPUT - REFINEMENT CHAIN")
                simple_log.info("LLM INPUT - REFINEMENT CHAIN")
                self.logger.info("="*250)
                simple_log.info("="*250)
                self.logger.info(f"Query: {query}")
                simple_log.info(f"Query: {query}")
                self.logger.info(f"Previous Draft: {state['draft']['content']}")
                simple_log.info(f"Previous Draft: {state['draft']['content']}")
                self.logger.info(f"Feedback: {feedback}")
                simple_log.info(f"Feedback: {feedback}")
                self.logger.info(f"Context: {context_str}")
                simple_log.info(f"Context: {context_str}")
                self.logger.info("="*250)
                simple_log.info("="*250)
                
                response = await self.refinement_chain.arun(
                    query=query,
                    previous_draft=state["draft"]["content"],
                    feedback=feedback,
                    context=context_str,
                    format_instructions=""  # We're using inline format instructions now
                )
                
                self.logger.info("="*250)
                simple_log.info("="*250)
                self.logger.info("LLM OUTPUT - REFINEMENT CHAIN")
                simple_log.info("LLM OUTPUT - REFINEMENT CHAIN")
                self.logger.info("="*250)
                simple_log.info("="*250)
                self.logger.info(f"Raw response: {response}")
                simple_log.info(f"Raw response: {response}")
                self.logger.info("="*250)
                simple_log.info("="*250)
            else:
                self.logger.info("Generating initial draft solution")
                simple_log.info("Generating initial draft solution")
                self.logger.info("Running CHAINED pipeline: Context Analysis → Draft Generation → Self-Assessment")
                simple_log.info("Running CHAINED pipeline: Context Analysis → Draft Generation → Self-Assessment")
                
                # Use the SEQUENTIAL PIPELINE!
                try:
                    pipeline_inputs = {
                        "query": query,
                        "context": context_str,
                        "feedback": feedback or "No previous feedback",
                        "course_prompt": course_prompt
                    }
                    
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    self.logger.info("LLM INPUT - DRAFT PIPELINE")
                    simple_log.info("LLM INPUT - DRAFT PIPELINE")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    try:
                        formatted_pipeline_inputs = json.dumps(pipeline_inputs, indent=2)
                        self.logger.info(f"Pipeline inputs (formatted):\n{formatted_pipeline_inputs}")
                        simple_log.info(f"Pipeline inputs (formatted):\n{formatted_pipeline_inputs}")
                    except:
                        self.logger.info(f"Pipeline inputs: {pipeline_inputs}")
                        simple_log.info(f"Pipeline inputs: {pipeline_inputs}")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    
                    pipeline_results = self.draft_pipeline.invoke(pipeline_inputs)
                    
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    self.logger.info("LLM OUTPUT - DRAFT PIPELINE")
                    simple_log.info("LLM OUTPUT - DRAFT PIPELINE")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    try:
                        formatted_pipeline_results = json.dumps(pipeline_results, indent=2)
                        self.logger.info(f"Pipeline results (formatted):\n{formatted_pipeline_results}")
                        simple_log.info(f"Pipeline results (formatted):\n{formatted_pipeline_results}")
                    except:
                        self.logger.info(f"Pipeline results: {pipeline_results}")
                        simple_log.info(f"Pipeline results: {pipeline_results}")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    
                    # Extract draft and quality assessment
                    response = pipeline_results.get("draft_output", "{}")
                    quality = pipeline_results.get("quality_assessment", "{}")
                    
                    # Log the quality assessment
                    try:
                        quality_json = json.loads(quality)
                        self.logger.info(f"Draft self-assessment: {quality_json.get('overall_quality', 'unknown')}")
                        simple_log.info(f"Draft self-assessment: {quality_json.get('overall_quality', 'unknown')}")
                        self.logger.info(f"  Completeness: {quality_json.get('completeness_score', 0):.2f}")
                        simple_log.info(f"  Completeness: {quality_json.get('completeness_score', 0):.2f}")
                        self.logger.info(f"  Context usage: {quality_json.get('context_usage_score', 0):.2f}")
                        simple_log.info(f"  Context usage: {quality_json.get('context_usage_score', 0):.2f}")
                        self.logger.info(f"  Clarity: {quality_json.get('clarity_score', 0):.2f}")
                        simple_log.info(f"  Clarity: {quality_json.get('clarity_score', 0):.2f}")
                    except:
                        pass
                        
                except Exception as e:
                    self.logger.warning(f"Pipeline failed, using direct generation: {e}")
                    # Fallback to direct generation
                    fallback_inputs = {
                        "query": query,
                        "context": context_str,
                        "feedback": feedback or "No previous feedback",
                        "course_prompt": course_prompt,
                        "context_insights": json.dumps({
                            "key_topics": ["Extracted from available context"],
                            "relationships": "Available context provides relevant information for answering the query", 
                            "suggested_approach": "Use the provided context to formulate a comprehensive response"
                        })  # Meaningful insights for fallback
                    }
                    
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    self.logger.info("LLM INPUT - DIRECT GENERATION FALLBACK")
                    simple_log.info("LLM INPUT - DIRECT GENERATION FALLBACK")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    try:
                        formatted_fallback_inputs = json.dumps(fallback_inputs, indent=2)
                        self.logger.info(f"Fallback inputs (formatted):\n{formatted_fallback_inputs}")
                        simple_log.info(f"Fallback inputs (formatted):\n{formatted_fallback_inputs}")
                    except:
                        self.logger.info(f"Fallback inputs: {fallback_inputs}")
                        simple_log.info(f"Fallback inputs: {fallback_inputs}")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    
                    response = await self.draft_generation_chain.arun(
                        query=query,
                        context=context_str,
                        feedback=feedback or "No previous feedback",
                        course_prompt=course_prompt,
                        context_insights=json.dumps({
                            "key_topics": ["Extracted from available context"],
                            "relationships": "Available context provides relevant information for answering the query",
                            "suggested_approach": "Use the provided context to formulate a comprehensive response"
                        })  # Meaningful insights for fallback
                    )
                    
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    self.logger.info("LLM OUTPUT - DIRECT GENERATION FALLBACK")
                    simple_log.info("LLM OUTPUT - DIRECT GENERATION FALLBACK")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
                    self.logger.info(f"Fallback response: {response}")
                    simple_log.info(f"Fallback response: {response}")
                    self.logger.info("="*250)
                    simple_log.info("="*250)
            
            # Parse structured output
            draft_content = None
            chain_of_thought = []
            
            try:
                # First try to parse as JSON directly
                try:
                    parsed_json = json.loads(response)
                    draft_content = parsed_json.get("draft_content", "")
                    
                    # Critical: Check for template placeholders or empty context claims
                    if self._contains_template_placeholders(draft_content):
                        self.logger.error("Draft contains template placeholders - generating proper content")
                        draft_content = self._generate_proper_answer(query, context_str)
                    elif "context does not contain" in draft_content.lower() or "context is empty" in draft_content.lower() or "no context available" in draft_content.lower():
                        self.logger.error(f"LLM claims empty context but we have {len(context_str)} chars of context - using fallback")
                        draft_content = self._generate_proper_answer(query, context_str)
                    
                    chain_of_thought = [
                        ChainOfThought(
                            step=step.get("step", i+1),
                            thought=step.get("thought", ""),
                            confidence=float(step.get("confidence", 0.7))
                        )
                        for i, step in enumerate(parsed_json.get("chain_of_thought", []))
                    ]
                except json.JSONDecodeError:
                    # Try to extract JSON from the response if it's embedded in text
                    json_match = re.search(r'\{[\s\S]*\}', response)
                    if json_match:
                        parsed_json = json.loads(json_match.group())
                        draft_content = parsed_json.get("draft_content", "")
                        
                        if self._contains_template_placeholders(draft_content):
                            self.logger.error("Draft contains template placeholders - generating proper content")
                            draft_content = self._generate_proper_answer(query, context_str)
                        elif "context does not contain" in draft_content.lower() or "context is empty" in draft_content.lower() or "no context available" in draft_content.lower():
                            self.logger.error(f"LLM claims empty context but we have {len(context_str)} chars of context - using fallback")
                            draft_content = self._generate_proper_answer(query, context_str)
                        
                        chain_of_thought = [
                            ChainOfThought(
                                step=step.get("step", i+1),
                                thought=step.get("thought", ""),
                                confidence=float(step.get("confidence", 0.7))
                            )
                            for i, step in enumerate(parsed_json.get("chain_of_thought", []))
                        ]
                    else:
                        raise ValueError("No valid JSON found in response")
            except Exception as e:
                self.logger.error(f"Failed to parse JSON output: {e}")
                raise ValueError(f"LLM output parsing failed: {e}")
            
            # Ensure we have valid content
            if not draft_content or self._contains_template_placeholders(draft_content):
                self.logger.error("Invalid draft content with template placeholders")
                raise ValueError("LLM generated invalid content with template placeholders")
            
            # Create draft object matching the specification
            draft = DraftContent(
                draft_id=f"d{state['current_round']}",  # Use round number for ID like spec
                content=draft_content,
                chain_of_thought=chain_of_thought,
                timestamp=datetime.now().isoformat()
            )
            
            # Also store as formatted JSON for logging
            formatted_output = {
                "draft_id": draft["draft_id"],
                "draft_content": draft["content"],
                "chain_of_thought": [
                    {
                        "step": step["step"],
                        "thought": step["thought"],
                        "confidence": step["confidence"]  # Include confidence score
                    }
                    for step in chain_of_thought
                ]
            }
            
            # Log the JSON output
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("STRATEGIST OUTPUT (JSON)")
            simple_log.info("STRATEGIST OUTPUT (JSON)")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(json.dumps(formatted_output, indent=2))
            simple_log.info(json.dumps(formatted_output, indent=2))
            self.logger.info("="*250)
            simple_log.info("="*250)

            # Send progress callback with draft details
            if self.context.progress_callback:
                try:
                    # Calculate average confidence from chain of thought
                    avg_confidence = sum(step["confidence"] for step in chain_of_thought) / len(chain_of_thought) if chain_of_thought else 0.0

                    progress_data = {
                        "status": "in_progress",
                        "stage": "strategist",
                        "message": f"✅ Draft generated ({len(draft_content)} chars, {len(chain_of_thought)} reasoning steps)",
                        "agent": "strategist",
                        "details": {
                            "type": "draft_complete",
                            "draft_id": draft["draft_id"],
                            "draft_length": len(draft_content),
                            "cot_steps": len(chain_of_thought),
                            "average_confidence": avg_confidence,
                            "reasoning_steps": [
                                {
                                    "step_number": step["step"],
                                    "thought": step["thought"],
                                    "confidence": step["confidence"]
                                }
                                for step in chain_of_thought[:5]  # Top 5 steps
                            ],
                            "round": state['current_round']
                        }
                    }
                    self.logger.info(f"Strategist: Sending progress update")
                    self.context.progress_callback(progress_data)
                except Exception as e:
                    self.logger.error(f"Failed to send strategist progress: {e}")

            # Update state
            state["draft"] = draft
            state["workflow_status"] = "debating"
            
            # Log execution
            processing_time = time.time() - start_time
            log_agent_execution(
                state=state,
                agent_name="Strategist",
                input_summary=f"Query: {query}, Round: {state['current_round']}",
                output_summary=f"Generated draft with {len(chain_of_thought)} CoT steps",
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Draft generated successfully:")
            simple_log.info(f"Draft generated successfully:")
            self.logger.info(f"  - Draft ID: {draft['draft_id']}")
            simple_log.info(f"  - Draft ID: {draft['draft_id']}")
            self.logger.info(f"  - Content length: {len(draft_content)} chars")
            simple_log.info(f"  - Content length: {len(draft_content)} chars")
            self.logger.info(f"  - CoT steps: {len(chain_of_thought)}")
            simple_log.info(f"  - CoT steps: {len(chain_of_thought)}")
            
            for i, step in enumerate(chain_of_thought, 1):  # All steps
                self.logger.info(f"  Step {i}: {step['thought']} (confidence: {step['confidence']:.2f})")
                simple_log.info(f"  Step {i}: {step['thought']} (confidence: {step['confidence']:.2f})")
            
        except Exception as e:
            self.logger.error(f"Draft generation failed: {str(e)}")
            state["error_messages"].append(f"Strategist agent error: {str(e)}")
            state["workflow_status"] = "failed"
            
            log_agent_execution(
                state=state,
                agent_name="Strategist",
                input_summary=f"Query: {state['query']}",
                output_summary=f"Error: {str(e)}",
                processing_time=time.time() - start_time,
                success=False
            )
        
        return state
    
    def _format_context(self, retrieval_results: List[Dict[str, Any]]) -> str:
        """Format retrieval results into context string"""
        if not retrieval_results:
            self.logger.warning("No retrieval results provided to format")
            return "No context available."
        
        context_parts = []
        for i, result in enumerate(retrieval_results, 1):  # All results
            # Handle both 'content' and 'text' fields for compatibility
            content = result.get('content', '') or result.get('text', '')
            score = result.get('score', 0.0)
            
            if not content:
                self.logger.warning(f"Result {i} has no content. Keys: {result.keys() if result else 'None'}")
                continue
                
            context_parts.append(
                f"[Source {i}] (Relevance: {score:.2f})\n"
                f"{content}\n"
            )
        
        if not context_parts:
            self.logger.error("All retrieval results were empty!")
            # Try to salvage something from the results
            self.logger.info(f"DEBUG: First result structure: {retrieval_results[0] if retrieval_results else 'No results'}")
            simple_log.info(f"DEBUG: First result structure: {retrieval_results[0] if retrieval_results else 'No results'}")
            return "Context retrieval failed - no readable content found."
        
        return "\n".join(context_parts)
    
    def _contains_template_placeholders(self, text: str) -> bool:
        """Check if text contains template placeholders"""
        # Check for common template patterns
        template_patterns = [
            r'\{query\}',
            r'\{context\}',
            r'\{[a-z_]+\}',  # Any lowercase placeholder
            r'\{.*_.*\}'     # Any placeholder with underscore
        ]
        
        for pattern in template_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _generate_proper_answer(self, query: str, context: str) -> str:
        """Generate a proper answer based on the actual context"""
        return self._generate_generic_answer(query, context)
    
    
    def _generate_generic_answer(self, query: str, context: str) -> str:
        """Generate a generic answer based on context"""
        # Extract key points from context
        lines = context.split('\n')
        key_points = []
        
        for line in lines:
            if line.strip() and not line.startswith('[Source') and len(line) > 20:
                key_points.append(line.strip())  # Keep full key point - no truncation
                if len(key_points) >= 5:
                    break
        
        answer = f"""Based on the retrieved information:

{chr(10).join(f'- {point}' for point in key_points)}

This information was retrieved from the course materials to answer your query: \"{query}\""""
        
        return answer
    
    
