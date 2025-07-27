"""
明示的な司会進行を行う司会者エージェント
"""
from typing import List, Dict, Any, Optional
from agents import Agent
import json


class FacilitatorAgent(Agent):
    """司会者として明示的に発言し、専門家への依頼を可視化するエージェント"""
    
    def __init__(self, expert_agents: List[Agent]):
        self.expert_agents = expert_agents
        self.expert_dict = {agent.name: agent for agent in expert_agents}
        
        expert_list = "\n".join([f"- {agent.name}: {agent.handoff_description}" for agent in expert_agents])
        
        instructions = f"""あなたは会議の司会者です。ユーザーの発言を受けて、適切に会議を進行してください。

利用可能な専門家:
{expert_list}

重要な指示：
1. 必ず「司会者です。」という立場表明から始めてください
2. まず状況を整理し、司会者としてコメントしてください
3. 専門的な内容の場合は、以下の形式で専門家を指名してください：
   
   【専門家指名】
   {{
     "expert": "専門家名",
     "question": "具体的な質問内容"
   }}

4. 一般的な内容や会議進行に関することは、あなたが直接回答してください

回答例1（自分で回答する場合）：
「司会者です。ご質問ありがとうございます。その点については、一般的に...（回答内容）」

回答例2（専門家に依頼する場合）：
「司会者です。Pythonのデコレータについてのご質問ですね。これは技術的な詳細が必要ですので、専門家にお聞きしましょう。

【専門家指名】
{{
  "expert": "Python Expert",
  "question": "Pythonのデコレータの仕組みと使用例について説明してください"
}}
」"""
        
        super().__init__(
            name="Facilitator",
            instructions=instructions,
            handoffs=[]  # handoffは使わない（明示的な指名を行うため）
        )
    
    def parse_expert_request(self, response: str) -> Optional[Dict[str, str]]:
        """司会者の応答から専門家への依頼を抽出"""
        if "【専門家指名】" not in response:
            return None
        
        try:
            # 【専門家指名】以降のJSON部分を抽出
            parts = response.split("【専門家指名】")
            if len(parts) < 2:
                return None
            
            json_str = parts[1].strip()
            # JSONの開始と終了を見つける
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            
            if start == -1 or end == 0:
                return None
            
            json_data = json_str[start:end]
            return json.loads(json_data)
        except Exception as e:
            print(f"専門家指名の解析エラー: {e}")
            return None