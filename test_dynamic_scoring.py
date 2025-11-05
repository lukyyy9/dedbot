#!/usr/bin/env python3
# test_dynamic_scoring.py
# Test du nouveau moteur de scoring dynamique

import sys
import logging
from core.config import ConfigManager
from core.scoring import ScoringEngine

logging.basicConfig(level=logging.INFO)

def test_scoring():
    """Teste le moteur de scoring dynamique."""
    
    print("\n" + "=" * 60)
    print("🧪 TEST DU MOTEUR DE SCORING DYNAMIQUE")
    print("=" * 60)
    
    # Charger la configuration
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Vérifier les formules chargées
    formulas = config.get("formulas", {})
    formula_weights = config.get("formula_weights", {})
    
    print(f"\n📊 Configuration chargée:")
    print(f"  - Formules définies: {len(formulas)}")
    print(f"  - Poids définis: {len(formula_weights)}")
    
    if not formulas:
        print("\n❌ ERREUR: Aucune formule définie dans la base de données!")
        print("💡 Exécutez d'abord: python migrate_formulas.py")
        return False
    
    print("\n📋 Formules actives:")
    for name, formula in formulas.items():
        weight = formula_weights.get(name, 0.0)
        print(f"  - {name}: poids={weight}")
        print(f"    Formule: {formula[:80]}{'...' if len(formula) > 80 else ''}")
    
    # Créer le moteur de scoring
    print("\n⚙️  Initialisation du moteur de scoring...")
    scoring_engine = ScoringEngine(config)
    
    # Tester avec un ticker
    ticker = "BTC-USD"
    print(f"\n🔍 Test de scoring pour {ticker}...")
    
    try:
        result = scoring_engine.compute_scores_for_ticker(ticker, period="90d")
        
        if result:
            print(f"\n✅ Score calculé avec succès!")
            print(f"  - Ticker: {result['ticker']}")
            print(f"  - Produit: {result['product_name']}")
            print(f"  - Score total: {result['score']}")
            print(f"  - Prix: {result['close']:.2f}")
            print(f"  - RSI14: {result['rsi14']}")
            
            print(f"\n📊 Scores par composant:")
            for name, score in result['components'].items():
                weight = formula_weights.get(name, 0.0)
                contribution = score * weight * 100
                print(f"  - {name}: {score:.3f} (poids: {weight}, contribution: {contribution:.1f})")
            
            # Vérifier que le score n'est pas à zéro
            if result['score'] == 0:
                print("\n⚠️  WARNING: Le score est à 0. Vérifiez les poids des formules.")
                return False
            
            print("\n✅ Test réussi!")
            return True
        else:
            print("\n❌ Aucun résultat retourné")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du calcul: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_scoring()
    sys.exit(0 if success else 1)
