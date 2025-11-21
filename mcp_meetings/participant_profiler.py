"""Participant profiler for generating mini profiles."""

import hashlib
import random
from typing import Dict, List, Optional


class ParticipantProfiler:
    """Generate profiles for meeting participants."""
    
    def __init__(self):
        """Initialize the profiler."""
        # Sample roles for profile generation
        self.roles = [
            "Software Engineer",
            "Product Manager",
            "Engineering Manager",
            "Senior Software Engineer",
            "Staff Engineer",
            "Principal Engineer",
            "Technical Lead",
            "UX Designer",
            "Product Designer",
            "Data Scientist",
            "DevOps Engineer",
            "Quality Assurance Engineer",
            "Solutions Architect",
            "Technical Program Manager",
            "Vice President of Engineering"
        ]
        
        # Sample departments
        self.departments = [
            "Engineering",
            "Product",
            "Design",
            "Data",
            "Operations",
            "Marketing",
            "Sales",
            "Customer Success"
        ]
        
        # Sample profile descriptions
        self.profile_templates = [
            "Experienced {role} with a passion for building scalable systems and mentoring team members.",
            "Results-driven {role} specializing in {specialty} and cross-functional collaboration.",
            "Creative {role} focused on {specialty} and delivering exceptional user experiences.",
            "Strategic {role} with expertise in {specialty} and a track record of successful product launches.",
            "Innovative {role} dedicated to {specialty} and driving technical excellence.",
            "Collaborative {role} with strong background in {specialty} and agile methodologies.",
            "Detail-oriented {role} passionate about {specialty} and continuous improvement.",
            "Visionary {role} committed to {specialty} and fostering a culture of innovation."
        ]
        
        # Sample specialties
        self.specialties = [
            "cloud infrastructure",
            "microservices architecture",
            "machine learning",
            "data analytics",
            "mobile development",
            "web development",
            "API design",
            "system optimization",
            "security best practices",
            "developer tools",
            "product strategy",
            "user research",
            "technical documentation",
            "automation",
            "performance optimization"
        ]
    
    def _get_deterministic_random(self, seed: str, choices: List[str]) -> str:
        """Get a deterministic random choice based on seed."""
        # Use hash of seed to get a deterministic "random" index
        hash_value = int(hashlib.md5(seed.encode()).hexdigest(), 16)
        index = hash_value % len(choices)
        return choices[index]
    
    def _generate_mini_profile(self, email: str, name: str) -> str:
        """
        Generate a mini profile/bio for a participant.
        
        Args:
            email: Email address of the participant
            name: Display name of the participant
        
        Returns:
            Mini profile string
        """
        # Use email as seed for deterministic profile generation
        role = self._get_deterministic_random(email, self.roles)
        specialty = self._get_deterministic_random(email + "_specialty", self.specialties)
        template = self._get_deterministic_random(email + "_template", self.profile_templates)
        
        # Generate profile
        profile = template.format(role=role, specialty=specialty)
        
        return profile
    
    def _extract_name(self, participant: Dict) -> str:
        """Extract display name from participant data."""
        if 'displayName' in participant and participant['displayName']:
            return participant['displayName']
        
        # Try to extract from email
        email = participant.get('email', '')
        if email:
            # Remove domain
            local_part = email.split('@')[0]
            # Convert to title case and replace dots/underscores with spaces
            name = local_part.replace('.', ' ').replace('_', ' ').title()
            return name
        
        return "Unknown"
    
    def _get_initials(self, name: str) -> str:
        """Get initials from a name."""
        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        elif len(parts) == 1 and len(parts[0]) >= 2:
            return parts[0][:2].upper()
        else:
            return "??"
    
    def _get_department(self, email: str, role: str) -> str:
        """Determine department based on role."""
        if "Engineer" in role or "DevOps" in role:
            return "Engineering"
        elif "Product" in role:
            return "Product"
        elif "Designer" in role or "UX" in role:
            return "Design"
        elif "Data" in role:
            return "Data"
        else:
            # Use email-based deterministic selection
            return self._get_deterministic_random(email + "_dept", self.departments)
    
    async def generate_profile(
        self, 
        participant: Dict, 
        include_mini_profile: bool = True
    ) -> Dict:
        """
        Generate a comprehensive profile for a participant.
        
        Args:
            participant: Participant data from calendar
            include_mini_profile: Whether to include the mini profile/bio
        
        Returns:
            Profile dictionary with participant information
        """
        email = participant.get('email', '')
        name = self._extract_name(participant)
        
        # Generate role
        role = self._get_deterministic_random(email, self.roles)
        
        # Build profile
        profile = {
            'email': email,
            'name': name,
            'initials': self._get_initials(name),
            'role': role,
            'department': self._get_department(email, role),
            'responseStatus': participant.get('responseStatus', 'needsAction'),
            'isOrganizer': participant.get('organizer', False),
            'isOptional': participant.get('optional', False)
        }
        
        # Add mini profile if requested
        if include_mini_profile:
            profile['miniProfile'] = self._generate_mini_profile(email, name)
        
        # Add contact info
        profile['contactInfo'] = {
            'email': email,
            'hasProfilePicture': False  # Would require additional API calls
        }
        
        return profile
    
    async def generate_profiles_batch(
        self,
        participants: List[Dict],
        include_mini_profile: bool = True
    ) -> List[Dict]:
        """
        Generate profiles for multiple participants.
        
        Args:
            participants: List of participant data
            include_mini_profile: Whether to include mini profiles
        
        Returns:
            List of profile dictionaries
        """
        profiles = []
        for participant in participants:
            profile = await self.generate_profile(participant, include_mini_profile)
            profiles.append(profile)
        
        return profiles
