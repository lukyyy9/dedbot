#!/bin/bash
# start-v2.sh - Script de démarrage rapide pour DedBot

echo "🤖 DedBot - Démarrage V2"
echo "========================="

# Vérifier que config.yaml existe
if [ ! -f "config.yaml" ]; then
    echo "❌ Erreur: config.yaml n'existe pas"
    echo "Veuillez créer un fichier config.yaml avec votre configuration"
    exit 1
fi

# Créer le répertoire data
mkdir -p data

# Arrêter les anciens conteneurs
echo "🛑 Arrêt des conteneurs..."
docker-compose down

# Construire l'image
echo "🔨 Construction de l'image Docker..."
docker build -t imluky/dedbot:latest .

# Démarrer le service
echo "🚀 Démarrage du service unifié..."
docker-compose up -d

echo ""
echo "✅ DedBot démarré avec succès !"
echo ""
echo "🌐 Interface Web & Bot : http://localhost:5001"
echo "   (Token d'admin configuré dans config.yaml)"
echo ""
echo "Commandes utiles:"
echo "  - Voir les logs           : docker-compose logs -f dedbot"
echo "  - Arrêter le service      : docker-compose down"
echo "  - Redémarrer              : docker-compose restart"
