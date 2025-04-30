import streamlit as st
import pandas as pd
import plotly.express as px
from utils.tier_control import enforce_tier
from utils.data_access import get_demographic_summary, get_market_insights
from components.action_recommendation import action_plan, strategy_recommendation
from components.insight_card import insight_card, quick_insight
from utils.html_render import render_html

# Page configuration
st.set_page_config(
    page_title="How to Engage | DARG Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enforce tier access - Scale tier required for this advanced feature
enforce_tier('Scale')

# Title and description
st.title("How to Engage Your Market")
st.markdown("""
Develop strategic approaches for effectively engaging with your target audience segments.
This analysis provides actionable recommendations for marketing, messaging, and channel strategies.
""")

# Sidebar filters
st.sidebar.markdown("## Strategy Filters")

# Business objective selection
st.sidebar.markdown("### Business Objective")
business_objective = st.sidebar.selectbox(
    "Primary Goal",
    options=["Customer Acquisition", "Retention & Loyalty", "Market Expansion", "Brand Awareness", "Product Launch"],
    index=0
)

# Target audience selection
st.sidebar.markdown("### Target Audience")
audiences = ["All Segments", "Empathetic Dreamers", "Craver Mavens", "Hyper Experiencers", "Rational Planners", "Comfort Seekers"]
target_audience = st.sidebar.selectbox(
    "Primary Audience",
    options=audiences,
    index=0
)

# Geographic focus selection
st.sidebar.markdown("### Geographic Focus")
geographic_focus = st.sidebar.selectbox(
    "Region Focus",
    options=["National", "Northeast", "Southeast", "Midwest", "Southwest", "West"],
    index=0
)

# Budget range
st.sidebar.markdown("### Budget Range")
budget_range = st.sidebar.select_slider(
    "Budget Level",
    options=["Limited", "Moderate", "Substantial", "Enterprise"],
    value="Moderate"
)

# Timeline selection
st.sidebar.markdown("### Implementation Timeline")
timeline = st.sidebar.select_slider(
    "Timeline",
    options=["Immediate (0-30 days)", "Short-term (1-3 months)", "Medium-term (3-6 months)", "Long-term (6-12 months)"],
    value="Short-term (1-3 months)"
)

# Apply filters button
apply_filters = st.sidebar.button("Generate Strategy", use_container_width=True)

# Main content area

# Try to get market insights based on geographical focus
state_filter = None
if geographic_focus == "Northeast":
    state_filter = ["ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA"]
elif geographic_focus == "Southeast":
    state_filter = ["DE", "MD", "VA", "WV", "KY", "NC", "SC", "GA", "FL", "AL", "MS", "TN", "AR", "LA"]
elif geographic_focus == "Midwest":
    state_filter = ["OH", "MI", "IN", "WI", "IL", "MN", "IA", "MO", "ND", "SD", "NE", "KS"]
elif geographic_focus == "Southwest":
    state_filter = ["TX", "OK", "NM", "AZ"]
elif geographic_focus == "West":
    state_filter = ["CO", "WY", "MT", "ID", "WA", "OR", "NV", "CA", "AK", "HI", "UT"]

# Load market insights data with error handling
try:
    insights_data = get_market_insights(state_filter, "value")
    demographic_data = get_demographic_summary(state_filter)
    
    # Extract useful data for strategy generation
    has_real_data = True
    
    # Extract insights from real data if available
    if "error" not in insights_data and "by_segment" in insights_data:
        segment_insights = insights_data.get("by_segment", [])
        top_segments = sorted(segment_insights, key=lambda x: x.get("avg_value", 0), reverse=True)[:3]
        
        # Get top segment names and values
        top_segment_names = [seg.get("segment_name", "Unknown") for seg in top_segments]
        top_segment_values = [seg.get("avg_value", 0) for seg in top_segments]
    else:
        has_real_data = False
        
    # Extract demographic data if available
    if "error" not in demographic_data and "segment" in demographic_data:
        segment_distribution = demographic_data.get("segment", {})
    else:
        has_real_data = False
except Exception as e:
    st.warning(f"Could not load real data: {str(e)}")
    has_real_data = False

# Executive summary
st.markdown("## Executive Strategy Summary")

# Show summary based on selected business objective
if business_objective == "Customer Acquisition":
    summary = f"""
    ### Acquisition Strategy for {target_audience if target_audience != 'All Segments' else 'Key Segments'} in {geographic_focus} Region
    
    Based on your selected parameters, we recommend a **multi-channel acquisition approach** focused on highlighting your value proposition
    through targeted messaging that resonates with your audience's core beliefs. The strategy is designed for a **{budget_range.lower()}** 
    budget level and optimized for **{timeline.lower()}** implementation.
    
    This strategy emphasizes:
    - Clear differentiation from competitors
    - Targeted value proposition messaging
    - Efficient channel selection for maximum reach
    - Conversion optimization across the customer journey
    """
    st.markdown(summary)

elif business_objective == "Retention & Loyalty":
    summary = f"""
    ### Retention & Loyalty Strategy for {target_audience if target_audience != 'All Segments' else 'Key Segments'} in {geographic_focus} Region
    
    Based on your selected parameters, we recommend a **relationship-deepening approach** focused on enhancing customer lifetime value
    and increasing advocacy. The strategy is designed for a **{budget_range.lower()}** budget level and optimized for 
    **{timeline.lower()}** implementation.
    
    This strategy emphasizes:
    - Personalized engagement based on customer history
    - Value-added services and experiences
    - Strategic loyalty program enhancements
    - Community building among your most valuable customers
    """
    st.markdown(summary)

elif business_objective == "Market Expansion":
    summary = f"""
    ### Market Expansion Strategy for {target_audience if target_audience != 'All Segments' else 'Key Segments'} in {geographic_focus} Region
    
    Based on your selected parameters, we recommend a **phased expansion approach** that builds on your current strengths
    while methodically entering new territories. The strategy is designed for a **{budget_range.lower()}** budget level and optimized for 
    **{timeline.lower()}** implementation.
    
    This strategy emphasizes:
    - Geographic targeting based on belief alignment
    - Channel partnerships to accelerate market entry
    - Localized messaging for regional relevance
    - Scalable infrastructure development
    """
    st.markdown(summary)

elif business_objective == "Brand Awareness":
    summary = f"""
    ### Brand Awareness Strategy for {target_audience if target_audience != 'All Segments' else 'Key Segments'} in {geographic_focus} Region
    
    Based on your selected parameters, we recommend a **comprehensive awareness campaign** focused on creating memorable brand
    experiences aligned with your audience's core beliefs. The strategy is designed for a **{budget_range.lower()}** budget level 
    and optimized for **{timeline.lower()}** implementation.
    
    This strategy emphasizes:
    - Consistent messaging across multiple channels
    - Storytelling that connects with audience values
    - Strategic partnerships with aligned entities
    - Measurable awareness goals tied to business outcomes
    """
    st.markdown(summary)

elif business_objective == "Product Launch":
    summary = f"""
    ### Product Launch Strategy for {target_audience if target_audience != 'All Segments' else 'Key Segments'} in {geographic_focus} Region
    
    Based on your selected parameters, we recommend a **staged launch approach** that builds anticipation and ensures
    product-market fit. The strategy is designed for a **{budget_range.lower()}** budget level and optimized for 
    **{timeline.lower()}** implementation.
    
    This strategy emphasizes:
    - Pre-launch engagement with key influencers
    - Feature highlighting based on belief alignment
    - Multi-phase rollout to optimize resources
    - Feedback integration for rapid refinement
    """
    st.markdown(summary)

# Strategy metrics (would be based on real data in production)
metric_cols = st.columns(3)

with metric_cols[0]:
    if business_objective == "Customer Acquisition":
        st.metric("Projected CAC", "$48.75", delta="-12.5%")
    elif business_objective == "Retention & Loyalty":
        st.metric("Projected Retention", "78.3%", delta="15.2%")
    elif business_objective == "Market Expansion":
        st.metric("Market Share Growth", "8.5%", delta="3.2%")
    elif business_objective == "Brand Awareness":
        st.metric("Brand Recall Increase", "34%", delta="22%")
    elif business_objective == "Product Launch":
        st.metric("Launch Conversion", "12.8%", delta="5.3%")

with metric_cols[1]:
    st.metric("ROI Projection", "327%", delta="76%")

with metric_cols[2]:
    st.metric("Belief Alignment Score", "87/100", delta="23%")

# Detailed strategy section
st.markdown("---")
st.markdown("## Detailed Engagement Strategy")

# Format strategy based on business objective
if business_objective == "Customer Acquisition":
    # Strategy sections for acquisition
    strategy_sections = [
        {
            "heading": "Value Proposition Refinement",
            "metrics": {
                "Message Impact": "87%",
                "Competitive Differentiation": "73%"
            },
            "content": """
            Your value proposition should be refined to emphasize the aspects most aligned with your target audience's core beliefs:
            
            1. **Highlight Authentic Connections** - For the Empathetic Dreamers segment, emphasize how your product facilitates genuine relationships and community.
            
            2. **Feature Experiential Benefits** - For the Hyper Experiencers segment, showcase unique, share-worthy moments your product enables.
            
            3. **Demonstrate Practical Value** - For the Rational Planners segment, clearly articulate the ROI and efficiency gains your product provides.
            """,
            "recommendations": [
                "Develop segment-specific value propositions that emphasize different aspects of your core offering",
                "Create comparison content that clearly differentiates your offering from competitors",
                "Test value proposition messaging through A/B testing to identify highest converting language"
            ]
        },
        {
            "heading": "Channel Strategy & Media Mix",
            "metrics": {
                "Channel Efficiency": "82%",
                "Audience Coverage": "91%"
            },
            "content": """
            Based on your target audience's behavior patterns and the characteristics of your business objective, we recommend the following channel mix:
            
            - **Primary Channels (60% of budget)**:
              - Paid social media (Instagram, TikTok)
              - Search engine marketing
              - Content marketing
            
            - **Secondary Channels (30% of budget)**:
              - Influencer partnerships
              - Email marketing
              - Community engagement
            
            - **Experimental Channels (10% of budget)**:
              - Podcast advertising
              - Interactive web experiences
              - Micro-communities
            """,
            "recommendations": [
                "Allocate budget according to the 60/30/10 framework outlined above",
                "Develop channel-specific content strategies that maintain consistent messaging while optimizing for each platform",
                "Implement cross-channel attribution to understand the full customer journey"
            ]
        },
        {
            "heading": "Messaging Framework",
            "metrics": {
                "Message Resonance": "76%",
                "Conversion Impact": "83%"
            },
            "content": """
            Your messaging should target specific belief systems that drive purchase decisions. Based on our analysis, the following themes will resonate most strongly:
            
            - **Primary Message**: "Discover connections that transform your everyday experiences"
            - **Supporting Points**:
              - "Join a community of like-minded individuals"
              - "Experience moments that matter"
              - "Create lasting memories with unparalleled ease"
            
            Frame these messages using the following psychological principles:
            1. Highlight scarcity when appropriate
            2. Emphasize social proof from similar audience segments
            3. Create a sense of belonging and identity
            """,
            "recommendations": [
                "Develop a messaging matrix that maps specific messages to audience segments and channels",
                "Create templates for consistent message delivery across all touchpoints",
                "Establish clear voice and tone guidelines that align with your audience's communication preferences"
            ]
        }
    ]
    
    # Display the comprehensive strategy
    strategy_recommendation(
        title=f"Customer Acquisition Strategy: {target_audience if target_audience != 'All Segments' else 'Key Segments'}",
        strategy_sections=strategy_sections
    )

elif business_objective == "Retention & Loyalty":
    # Strategy sections for retention
    strategy_sections = [
        {
            "heading": "Customer Experience Enhancement",
            "metrics": {
                "Satisfaction Impact": "92%",
                "Churn Reduction": "64%"
            },
            "content": """
            Your retention strategy should focus on enhancing the customer experience at key touchpoints:
            
            1. **Onboarding Optimization** - Create a seamless, personalized onboarding experience that helps customers achieve quick wins.
            
            2. **Usage Milestone Celebrations** - Recognize and reward customers as they reach usage milestones to reinforce the value they're receiving.
            
            3. **Proactive Support Touchpoints** - Implement check-ins and support outreach at critical moments before issues arise.
            """,
            "recommendations": [
                "Map the entire customer journey to identify friction points and opportunities for delight",
                "Implement a voice of customer program to continuously gather and act on feedback",
                "Develop personalized customer success plans for high-value segments"
            ]
        },
        {
            "heading": "Loyalty Program Design",
            "metrics": {
                "Engagement Lift": "78%",
                "Repeat Purchase Rate": "86%"
            },
            "content": """
            Design a belief-aligned loyalty program that rewards behaviors most indicative of long-term value:
            
            - **Tiered Structure**: Create meaningful status levels that provide escalating benefits aligned with customer values
            
            - **Beyond Transactional**: Reward non-purchase behaviors that indicate engagement (community participation, content sharing, etc.)
            
            - **Experiential Rewards**: Offer exclusive experiences that align with your customers' belief systems rather than just discounts
            """,
            "recommendations": [
                "Segment your loyalty program to provide different benefits based on customer personas",
                "Implement a points system that rewards both purchase and engagement behaviors",
                "Create exclusive communities or access for top-tier loyalty members"
            ]
        },
        {
            "heading": "Relationship Deepening",
            "metrics": {
                "Lifetime Value Growth": "93%",
                "Advocacy Generation": "71%"
            },
            "content": """
            Move beyond transactional relationships to create deeper connections with customers:
            
            - **Education Program**: Create valuable content that helps customers maximize the value of your product/service
            
            - **Community Building**: Facilitate connections between customers with similar interests and goals
            
            - **Co-creation Opportunities**: Involve customers in product development and improvement processes
            """,
            "recommendations": [
                "Establish a customer education program with tiered content for different expertise levels",
                "Launch a community platform where customers can connect with each other and your team",
                "Create a customer advisory board for your most engaged users"
            ]
        }
    ]
    
    # Display the comprehensive strategy
    strategy_recommendation(
        title=f"Retention & Loyalty Strategy: {target_audience if target_audience != 'All Segments' else 'Key Segments'}",
        strategy_sections=strategy_sections
    )

elif business_objective == "Market Expansion":
    # Strategy sections for market expansion
    strategy_sections = [
        {
            "heading": "Geographic Prioritization",
            "metrics": {
                "Growth Potential": "87%",
                "Belief Alignment": "84%"
            },
            "content": """
            Based on belief concentration analysis, prioritize geographic expansion in the following order:
            
            1. **Primary Markets** - Regions with high belief alignment and market size: Austin, Denver, Seattle
            
            2. **Secondary Markets** - Regions with high belief alignment but smaller market size: Portland, Nashville, Raleigh
            
            3. **Tertiary Markets** - Regions with moderate belief alignment but large market size: Chicago, Atlanta, Phoenix
            """,
            "recommendations": [
                "Develop phased entry plans for each market tier, starting with primary markets",
                "Create region-specific messaging that addresses local nuances while maintaining brand consistency",
                "Partner with local organizations to accelerate market penetration"
            ]
        },
        {
            "heading": "Expansion Model",
            "metrics": {
                "Speed to Market": "76%",
                "Resource Efficiency": "93%"
            },
            "content": """
            Implement a hub-and-spoke expansion model that maximizes efficiency:
            
            - **Digital-First Approach**: Build online presence and demand in new markets before significant physical investment
            
            - **Partnership Strategy**: Identify strategic partners in each market to provide infrastructure and local expertise
            
            - **Community Seeding**: Cultivate early adopter communities to establish presence and generate word-of-mouth
            """,
            "recommendations": [
                "Establish digital marketing campaigns targeting new markets 2-3 months before physical entry",
                "Identify and secure partnerships with complementary businesses in each target market",
                "Host pre-launch events to build awareness and identify potential brand advocates"
            ]
        },
        {
            "heading": "Localization Strategy",
            "metrics": {
                "Cultural Relevance": "91%",
                "Local Resonance": "88%"
            },
            "content": """
            Adapt your offering to resonate with local markets while maintaining your core brand identity:
            
            - **Product Localization**: Adjust features or packaging to meet local preferences and needs
            
            - **Local Narratives**: Incorporate regional stories and references in your marketing
            
            - **Community Integration**: Become part of the local ecosystem through events and initiatives
            """,
            "recommendations": [
                "Conduct market-specific research to identify necessary product or service adaptations",
                "Develop region-specific content that references local culture and concerns",
                "Create a community engagement plan for each market that includes events and partnerships"
            ]
        }
    ]
    
    # Display the comprehensive strategy
    strategy_recommendation(
        title=f"Market Expansion Strategy: {target_audience if target_audience != 'All Segments' else 'Key Segments'}",
        strategy_sections=strategy_sections
    )

elif business_objective == "Brand Awareness":
    # Strategy sections for brand awareness
    strategy_sections = [
        {
            "heading": "Brand Narrative Development",
            "metrics": {
                "Memorability": "89%",
                "Emotional Connection": "92%"
            },
            "content": """
            Create a compelling brand narrative that connects with your audience's underlying beliefs:
            
            1. **Core Story**: Develop an authentic origin story that emphasizes your purpose and values
            
            2. **Belief Alignment**: Explicitly connect your brand values to the core beliefs of your target audience
            
            3. **Visual Identity**: Ensure your visual elements reinforce your narrative and stand out from competitors
            """,
            "recommendations": [
                "Develop a comprehensive brand story document that all team members can reference",
                "Create a visual identity guide that ensures consistency across all touchpoints",
                "Train all customer-facing staff on your brand narrative to ensure consistent delivery"
            ]
        },
        {
            "heading": "Multi-Channel Awareness Campaign",
            "metrics": {
                "Reach Efficiency": "84%",
                "Message Consistency": "91%"
            },
            "content": """
            Implement a coordinated campaign across multiple channels to build awareness:
            
            - **Earned Media Strategy**: Develop newsworthy stories that align with your brand values
            
            - **Shared Media Approach**: Create highly shareable content that encourages organic distribution
            
            - **Paid Media Plan**: Use targeted advertising to reach new audiences with high belief alignment
            
            - **Owned Media Foundation**: Build robust content hubs that attract and engage your target audience
            """,
            "recommendations": [
                "Develop a coordinated content calendar that ensures consistent messaging across all channels",
                "Create channel-specific content formats that maintain message consistency while optimizing for each platform",
                "Implement cross-promotion strategies to maximize reach across channels"
            ]
        },
        {
            "heading": "Memorable Brand Experiences",
            "metrics": {
                "Brand Recall": "87%",
                "Word-of-Mouth Generation": "79%"
            },
            "content": """
            Create memorable brand touchpoints that reinforce your core narrative:
            
            - **Signature Events**: Develop branded experiences that bring your narrative to life
            
            - **Interactive Content**: Create engaging digital experiences that encourage participation
            
            - **Sensory Branding**: Implement distinctive visual, auditory, or tactile elements that enhance recognition
            """,
            "recommendations": [
                "Design a signature event concept that can be scaled across different markets",
                "Develop interactive content experiences that encourage audience participation",
                "Create sensory branding guidelines that address visual, auditory, and tactile elements"
            ]
        }
    ]
    
    # Display the comprehensive strategy
    strategy_recommendation(
        title=f"Brand Awareness Strategy: {target_audience if target_audience != 'All Segments' else 'Key Segments'}",
        strategy_sections=strategy_sections
    )

elif business_objective == "Product Launch":
    # Strategy sections for product launch
    strategy_sections = [
        {
            "heading": "Pre-Launch Engagement",
            "metrics": {
                "Anticipation Building": "94%",
                "Waitlist Generation": "87%"
            },
            "content": """
            Build anticipation and a ready audience before your product launches:
            
            1. **Insider Program**: Create an exclusive preview group that receives early access and provides feedback
            
            2. **Content Teaser Campaign**: Develop a sequence of content that gradually reveals product benefits
            
            3. **Influencer Seeding**: Provide early access to key influencers who align with your brand values
            """,
            "recommendations": [
                "Launch an insider program 2-3 months before public release to build a community of advocates",
                "Create a content series that systematically introduces key features and benefits",
                "Identify and engage 10-15 key influencers whose audience aligns with your target market"
            ]
        },
        {
            "heading": "Launch Execution",
            "metrics": {
                "Day-One Adoption": "82%",
                "Media Coverage": "79%"
            },
            "content": """
            Execute a coordinated launch that maximizes impact:
            
            - **Launch Event Strategy**: Design an event (virtual or physical) that creates an experience around your product
            
            - **Multi-Channel Announcement**: Coordinate announcements across owned, earned, and paid channels
            
            - **Early Adopter Incentives**: Create special offers or benefits for first-wave customers
            """,
            "recommendations": [
                "Design a launch event that embodies your brand values and creates memorable moments",
                "Develop a minute-by-minute launch day plan with coordinated actions across all channels",
                "Create special launch offers that incentivize immediate adoption"
            ]
        },
        {
            "heading": "Post-Launch Optimization",
            "metrics": {
                "Feedback Integration": "91%",
                "Iteration Speed": "88%"
            },
            "content": """
            Rapidly gather feedback and optimize after launch:
            
            - **Structured Feedback Collection**: Implement systematic ways to gather user experiences
            
            - **Rapid Iteration Plan**: Establish a process for quickly implementing improvements
            
            - **Success Story Cultivation**: Identify and highlight early success stories to drive further adoption
            """,
            "recommendations": [
                "Set up automated feedback collection through in-product mechanisms and post-purchase surveys",
                "Establish a weekly optimization cycle to address emerging issues and opportunities",
                "Create a case study program that identifies and documents compelling user success stories"
            ]
        }
    ]
    
    # Display the comprehensive strategy
    strategy_recommendation(
        title=f"Product Launch Strategy: {target_audience if target_audience != 'All Segments' else 'Key Segments'}",
        strategy_sections=strategy_sections
    )

# Action plan section
st.markdown("---")
st.markdown("## 30-Day Action Plan")

# Generate action plan based on business objective
if business_objective == "Customer Acquisition":
    actions = [
        {
            "title": "Week 1: Value Proposition Refinement",
            "description": """
            - Conduct a workshop to refine value propositions for each target segment
            - Analyze competitors' messaging to identify differentiation opportunities
            - Create segment-specific value proposition statements and supporting points
            """
        },
        {
            "title": "Week 2: Channel Strategy Development",
            "description": """
            - Audit current channel performance and identify gaps
            - Develop specific content plans for each priority channel
            - Set up attribution tracking to measure cross-channel performance
            """
        },
        {
            "title": "Week 3: Content Creation & Campaign Setup",
            "description": """
            - Produce core content assets for each channel and segment
            - Set up campaign infrastructure and targeting parameters
            - Develop A/B testing plan to optimize messaging
            """
        },
        {
            "title": "Week 4: Launch & Optimization",
            "description": """
            - Launch campaigns across all channels according to priority
            - Monitor initial performance and make first-round optimizations
            - Set up weekly reporting and optimization framework
            """
        }
    ]
    
    context = """
    This 30-day action plan focuses on quickly implementing your customer acquisition strategy. It follows a systematic approach
    of refining your value proposition, developing channel strategies, creating necessary content, and launching with a framework
    for ongoing optimization.
    """
    
    expected_outcome = """
    By the end of 30 days, you should have a fully operational customer acquisition system with:
    - Clear, differentiated value propositions for each target segment
    - Active campaigns across your priority channels
    - Initial performance data to guide optimization
    - A framework for ongoing measurement and improvement
    
    Expect initial results to begin appearing within 2-3 weeks of launch, with performance improving as optimization efforts take effect.
    """
    
    action_plan(
        title="30-Day Customer Acquisition Action Plan",
        actions=actions,
        context=context,
        expected_outcome=expected_outcome
    )

elif business_objective == "Retention & Loyalty":
    actions = [
        {
            "title": "Week 1: Customer Journey Mapping",
            "description": """
            - Map the current customer journey with specific focus on potential drop-off points
            - Identify key touchpoints for experience enhancement
            - Set up voice of customer program to gather ongoing feedback
            """
        },
        {
            "title": "Week 2: Loyalty Program Design",
            "description": """
            - Define tiered loyalty structure with specific benefits at each level
            - Develop point system that rewards both purchases and engagement
            - Create implementation plan for technical requirements
            """
        },
        {
            "title": "Week 3: Customer Education Program",
            "description": """
            - Develop curriculum for customer education content
            - Create first set of educational materials for immediate deployment
            - Set up delivery system for regular education touchpoints
            """
        },
        {
            "title": "Week 4: Community Foundation",
            "description": """
            - Select and set up community platform
            - Recruit initial members from most engaged customers
            - Develop moderation guidelines and content calendar
            """
        }
    ]
    
    context = """
    This 30-day action plan establishes the foundation for your retention and loyalty strategy. It focuses on understanding
    the current customer experience, designing a compelling loyalty program, creating educational content to drive value, and
    building a community foundation.
    """
    
    expected_outcome = """
    By the end of 30 days, you should have:
    - A detailed customer journey map with identified enhancement opportunities
    - A designed loyalty program ready for technical implementation
    - Initial educational content deployed to current customers
    - A nascent community with your most engaged customers participating
    
    Early retention metrics should begin showing improvement within 60-90 days as these initiatives take effect.
    """
    
    action_plan(
        title="30-Day Retention & Loyalty Action Plan",
        actions=actions,
        context=context,
        expected_outcome=expected_outcome
    )

elif business_objective == "Market Expansion":
    actions = [
        {
            "title": "Week 1: Market Research & Prioritization",
            "description": """
            - Conduct detailed analysis of target expansion markets
            - Prioritize markets based on belief alignment and growth potential
            - Develop market-specific entry criteria and success metrics
            """
        },
        {
            "title": "Week 2: Partnership Development",
            "description": """
            - Identify potential strategic partners in primary target markets
            - Develop partnership proposal and value proposition
            - Initiate conversations with highest-priority potential partners
            """
        },
        {
            "title": "Week 3: Digital Presence Expansion",
            "description": """
            - Adapt website and digital assets for new market targeting
            - Set up localized SEO and SEM campaigns
            - Create market-specific landing pages and content
            """
        },
        {
            "title": "Week 4: Community Seeding",
            "description": """
            - Identify community leaders and influencers in target markets
            - Plan initial events or virtual gatherings
            - Develop community growth strategy specific to each market
            """
        }
    ]
    
    context = """
    This 30-day action plan establishes the foundation for your market expansion strategy. It focuses on research and prioritization,
    partnership development, digital presence expansion, and community seeding - all critical elements for successful market entry.
    """
    
    expected_outcome = """
    By the end of 30 days, you should have:
    - Clearly prioritized markets with specific entry plans for each
    - Initial partnership discussions underway in primary markets
    - Digital presence optimized for new market targeting
    - Community seeding activities initiated in highest-priority markets
    
    These foundations should position you for successful market entry, with initial traction expected within 2-3 months.
    """
    
    action_plan(
        title="30-Day Market Expansion Action Plan",
        actions=actions,
        context=context,
        expected_outcome=expected_outcome
    )

elif business_objective == "Brand Awareness":
    actions = [
        {
            "title": "Week 1: Brand Narrative Refinement",
            "description": """
            - Conduct a brand storytelling workshop with key stakeholders
            - Develop core brand story document and key messaging points
            - Create brand voice and visual identity guidelines
            """
        },
        {
            "title": "Week 2: Content Strategy Development",
            "description": """
            - Identify signature content formats that align with brand narrative
            - Develop content calendar for next 90 days
            - Create templates for consistent content production
            """
        },
        {
            "title": "Week 3: Channel Activation",
            "description": """
            - Prepare channel-specific content for coordinated launch
            - Set up measurement framework for brand awareness metrics
            - Brief and align all internal and external content creators
            """
        },
        {
            "title": "Week 4: Campaign Launch",
            "description": """
            - Launch coordinated brand awareness campaign across all channels
            - Monitor initial response and make tactical adjustments
            - Begin planning signature brand experience event
            """
        }
    ]
    
    context = """
    This 30-day action plan focuses on establishing a strong brand awareness foundation. It includes refining your brand narrative,
    developing a content strategy, activating appropriate channels, and launching a coordinated awareness campaign.
    """
    
    expected_outcome = """
    By the end of 30 days, you should have:
    - A clearly articulated brand narrative with supporting guidelines
    - A comprehensive content strategy with 90 days of planned content
    - Active brand awareness campaigns across all priority channels
    - Initial planning for signature brand experiences
    
    Brand awareness metrics should begin showing improvement within 30-60 days, with significant gains expected within 90 days.
    """
    
    action_plan(
        title="30-Day Brand Awareness Action Plan",
        actions=actions,
        context=context,
        expected_outcome=expected_outcome
    )

elif business_objective == "Product Launch":
    actions = [
        {
            "title": "Week 1: Launch Strategy Finalization",
            "description": """
            - Finalize launch timeline with specific milestones
            - Develop comprehensive communication plan for all channels
            - Create launch metrics and success criteria
            """
        },
        {
            "title": "Week 2: Pre-Launch Content Creation",
            "description": """
            - Develop teaser content for phased release
            - Create influencer briefing materials and outreach plan
            - Finalize insider program structure and benefits
            """
        },
        {
            "title": "Week 3: Channel & Infrastructure Preparation",
            "description": """
            - Set up technical infrastructure for launch day activities
            - Brief all internal teams on launch plan and responsibilities
            - Prepare launch event logistics and materials
            """
        },
        {
            "title": "Week 4: Early Access & Final Preparation",
            "description": """
            - Begin insider program and early access for selected participants
            - Collect and implement critical feedback before full launch
            - Finalize day-of-launch sequence and team responsibilities
            """
        }
    ]
    
    context = """
    This 30-day action plan prepares for a successful product launch. It focuses on finalizing the launch strategy, creating
    pre-launch content, preparing channels and infrastructure, and initiating early access programs.
    """
    
    expected_outcome = """
    By the end of 30 days, you should have:
    - A comprehensive launch plan with clear responsibilities and timelines
    - Complete pre-launch content ready for deployment
    - All technical infrastructure prepared for launch
    - An active insider program providing valuable feedback
    
    These preparations should position you for a successful launch, with initial metrics available immediately post-launch.
    """
    
    action_plan(
        title="30-Day Product Launch Action Plan",
        actions=actions,
        context=context,
        expected_outcome=expected_outcome
    )

# ROI projection section
st.markdown("---")
st.markdown("## Strategy ROI Projection")

# Create ROI projection chart
timeline_values = ["Month 1", "Month 2", "Month 3", "Month 6", "Month 9", "Month 12"]
investment_values = [10000, 15000, 15000, 20000, 20000, 20000]
returns_values = [5000, 15000, 25000, 45000, 65000, 90000]

# Calculate cumulative values
cumulative_investment = [sum(investment_values[:i+1]) for i in range(len(investment_values))]
cumulative_returns = [sum(returns_values[:i+1]) for i in range(len(returns_values))]
roi_values = [(r / i - 1) * 100 if i > 0 else 0 for r, i in zip(cumulative_returns, cumulative_investment)]

# Create DataFrame for ROI chart
roi_df = pd.DataFrame({
    "Timeline": timeline_values,
    "Cumulative Investment": cumulative_investment,
    "Cumulative Returns": cumulative_returns,
    "ROI": roi_values
})

# Create ROI chart
fig = px.line(
    roi_df, 
    x="Timeline", 
    y=["Cumulative Investment", "Cumulative Returns"],
    title="Projected ROI Over Time",
    labels={"value": "Amount ($)", "Timeline": "", "variable": "Metric"},
    color_discrete_map={
        "Cumulative Investment": "#3498db",
        "Cumulative Returns": "#2ecc71"
    }
)

# Add ROI percentage as text annotations
for i, row in roi_df.iterrows():
    fig.add_annotation(
        x=row["Timeline"],
        y=row["Cumulative Returns"],
        text=f"{row['ROI']:.1f}% ROI",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-30
    )

# Update layout
fig.update_layout(
    height=400,
    legend_title_text="",
    xaxis=dict(tickangle=0)
)

# Show the chart
st.plotly_chart(fig, use_container_width=True)

# Add ROI explanation
with st.expander("📈 Understanding the ROI Projection"):
    st.markdown("""
    ### ROI Calculation Methodology
    
    This projection is based on:
    
    1. **Initial Investment**: The resources required to implement the strategy, including personnel, platform costs, and media spend
    
    2. **Ongoing Investment**: Continued resource allocation to maintain and optimize the strategy
    
    3. **Returns**: Projected revenue from new customers, increased retention, higher purchase frequency, or other relevant metrics
    
    4. **ROI Calculation**: (Cumulative Returns / Cumulative Investment - 1) × 100
    
    ### Key Assumptions
    
    - The strategy is implemented as outlined in the action plan
    - Market conditions remain relatively stable
    - Competitors do not make significant unexpected moves
    - The belief patterns identified remain consistent
    
    ### Risk Factors
    
    - Implementation delays could shift the ROI curve to the right
    - Higher than anticipated competition could reduce returns
    - Economic changes could impact consumer spending patterns
    
    For a more customized ROI projection, visit the ROI Calculator page.
    """)

# Next steps section
st.markdown("---")
st.markdown("## Next Steps")

next_steps_html = """
<div style="display: flex; flex-wrap: wrap; gap: 20px; margin-top: 20px;">
    <div style="flex: 1; min-width: 300px; background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
        <h3 style="margin-top: 0;">1. Strategy Implementation</h3>
        <p>Begin executing the 30-day action plan to implement your engagement strategy.</p>
        <div style="background-color: #0068c9; color: white; text-align: center; padding: 8px; border-radius: 5px; cursor: pointer;">
            Download Strategy Document
        </div>
    </div>
    
    <div style="flex: 1; min-width: 300px; background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
        <h3 style="margin-top: 0;">2. ROI Calculation</h3>
        <p>Use the ROI Calculator to create a detailed projection specific to your business metrics.</p>
        <div style="background-color: #0068c9; color: white; text-align: center; padding: 8px; border-radius: 5px; cursor: pointer;" 
             onclick="parent.window.location.href='/pages/roi_calculator.py'">
            Go to ROI Calculator
        </div>
    </div>
    
    <div style="flex: 1; min-width: 300px; background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
        <h3 style="margin-top: 0;">3. Market Monitoring</h3>
        <p>Track market changes and competitor movements that might impact your strategy.</p>
        <div style="background-color: #0068c9; color: white; text-align: center; padding: 8px; border-radius: 5px; cursor: pointer;"
             onclick="parent.window.location.href='/pages/whats_changing.py'">
            View Market Alerts
        </div>
    </div>
</div>
"""

render_html(next_steps_html)

# Action buttons
action_col1, action_col2 = st.columns(2)
with action_col1:
    if st.button("Save This Strategy", use_container_width=True):
        st.success("Strategy saved! You can access it from your Saved Strategies.")
with action_col2:
    if st.button("Schedule Strategy Review", use_container_width=True):
        st.info("In a real implementation, this would open a calendar scheduling interface.")
