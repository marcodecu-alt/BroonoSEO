"""One-time seed of existing_content_index from Broono's published blog articles.

Titles/keywords/summaries here were pulled manually from
https://www.broono.pet/blogs/dog-health-articles on 2026-07-08. Re-run with
updated entries whenever new articles are published (see README: this is a
manual one-time scrape for now, not scheduled).

Run from apps/api with the venv active:
    python scripts/seed_content_index.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.supabase_client import supabase

articles = [
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/joint-ageing-hub",
        "title": "Signs your dog's joints are ageing",
        "target_keyword": "dog joint aging signs",
        "summary": "Early indicators of joint deterioration in dogs (stiffness after rest, hesitation on stairs, slower pace), distinguishing gradual aging changes from acute injury, and evidence-based supplements (glucosamine, chondroitin, boswellia).",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/dog-supplements-fill-nutritional-gaps",
        "title": "Dog Nutritional Gaps: Do You Need to Supplement?",
        "target_keyword": "dog nutritional gaps supplements",
        "summary": "How commercial dog food loses nutritional potency during processing, common deficiencies (omega-3s, B vitamins, minerals), and how targeted supplementation addresses them.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/magnesium-choosing-the-right-form-for-relaxation-in-dogs",
        "title": "Magnesium for Dogs: Choosing the Right Form",
        "target_keyword": "magnesium for dogs",
        "summary": "Comparison of magnesium forms for canine health, muscle function, nerve transmission and mood, highlighting magnesium bisglycinate for calming effects.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/how-to-keep-your-dog-thriving-through-winter",
        "title": "How to Keep Your Dog Thriving Through Winter",
        "target_keyword": "winter dog health",
        "summary": "How cold weather challenges a dog's immune system, and strategies (vitamin C/E, exercise, diet, hydration) to keep dogs healthy through winter.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/the-calming-power-of-l-theanine-for-dogs",
        "title": "The Calming Power of L-Theanine for Dogs: Enhancing Sleep and Focus",
        "target_keyword": "l-theanine for dogs",
        "summary": "How L-theanine promotes canine relaxation and sleep quality without sedation, and daytime mental clarity benefits.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/the-science-behind-prebiotics",
        "title": "The Science Behind Prebiotics",
        "target_keyword": "prebiotics for dogs",
        "summary": "Why prebiotics (food for existing gut bacteria) offer more sustainable gut health results for dogs than probiotics, supporting digestion and immune function.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/the-importance-of-a-holistic-approach-to-dog-health",
        "title": "The Importance of a Holistic Approach to Dog Health",
        "target_keyword": "holistic dog health",
        "summary": "Addressing physical, emotional, and mental well-being together via nutrition, exercise, mental stimulation, and preventive care.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/how-dog-supplements-work-1",
        "title": "Why Your Dog Needs the Best Supplements",
        "target_keyword": "dog supplements benefits",
        "summary": "How supplements fill dietary gaps and target joint mobility, digestive health, and mental well-being; importance of quality ingredients and dosing.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/the-marvelous-benefits-of-superoxide-dismutase",
        "title": "The Marvelous Benefits of Superoxide Dismutase",
        "target_keyword": "superoxide dismutase for dogs",
        "summary": "How the SOD enzyme combats free radicals and oxidative stress in dogs, benefiting joints, skin, and cognitive function.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/beat-the-heat-ensuring-your-pup-stays-cool-this-summer",
        "title": "Beat the Heat Ensuring Your Pup Stays Cool",
        "target_keyword": "keep dogs cool in summer",
        "summary": "Practical summer heat safety steps for dog owners: walk timing, hydration, recognizing heat stroke symptoms, and cooling alternatives.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/the-benefits-of-vitamin-b-complex-supplements-for-dogs",
        "title": "The Benefits of B Vitamins for Dogs",
        "target_keyword": "vitamin b complex for dogs",
        "summary": "Roles of the eight B vitamins in canine energy production, nervous system function, and immune support.",
    },
    {
        "url": "https://www.broono.pet/blogs/dog-health-articles/the-glorious-trio-msm-glucosamine-and-chondroitin",
        "title": "The Glorious Trio: MSM, Glucosamine, and Chondroitin",
        "target_keyword": "msm glucosamine chondroitin for dogs",
        "summary": "How glucosamine, chondroitin, and MSM each support canine joint health, cartilage, and inflammation, for pain relief and mobility.",
    },
]

if __name__ == "__main__":
    resp = supabase.table("existing_content_index").upsert(articles, on_conflict="url").execute()
    print(f"upserted {len(resp.data)} rows")
