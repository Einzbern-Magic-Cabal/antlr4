package org.antlr.v4.automata;

import org.antlr.v4.tool.Grammar;
import org.antlr.v4.tool.Rule;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** */
public class NFA {
	public Grammar g;
	public List<NFAState> states = new ArrayList<NFAState>();

	/** Each subrule/rule is a decision point and we must track them so we
	 *  can go back later and build DFA predictors for them.  This includes
	 *  all the rules, subrules, optional blocks, ()+, ()* etc...
	 */
	public List<DecisionState> decisionToNFAState = new ArrayList<DecisionState>();

	public Map<Rule, RuleStartState> ruleToStartState = new LinkedHashMap<Rule, RuleStartState>();
	public Map<Rule, RuleStopState> ruleToStopState = new LinkedHashMap<Rule, RuleStopState>();

	int stateNumber = 0;
	
	public NFA(Grammar g) { this.g = g; }

	public void addState(NFAState state) {
		states.add(state);
		state.stateNumber = stateNumber++;
	}

	public int defineDecisionState(DecisionState s) {
		decisionToNFAState.add(s);
		return decisionToNFAState.size()-1;
	}
}