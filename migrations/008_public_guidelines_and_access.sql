-- Migration: Public Guidelines and Organization Access Control
-- Description: Add support for public guidelines with three-tier access control
-- Author: ABCD Team
-- Date: 2025-10-07

-- ============================================================================
-- 1. Add public guideline support to existing guidelines table
-- ============================================================================

-- Add email domain mapping to organizations
ALTER TABLE organizations 
ADD COLUMN IF NOT EXISTS email_domains JSONB DEFAULT '[]';

COMMENT ON COLUMN organizations.email_domains IS 
'List of email domains that belong to this organization, e.g., ["unicef.org", "unicef.ch"]';

-- Add public/visibility fields to guidelines
ALTER TABLE organization_guidelines 
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS visibility_scope VARCHAR(50) DEFAULT 'organization';

COMMENT ON COLUMN organization_guidelines.is_public IS 
'Whether this guideline is publicly shareable across organizations';

COMMENT ON COLUMN organization_guidelines.visibility_scope IS 
'Visibility: organization (default), public_mapped (admin-controlled), universal (all orgs)';

-- ============================================================================
-- 2. Create organization-to-guideline access mapping table
-- ============================================================================

CREATE TABLE IF NOT EXISTS organization_guideline_access (
    id SERIAL PRIMARY KEY,
    organization_id VARCHAR(255) NOT NULL,
    guideline_id VARCHAR(255) NOT NULL,
    granted_by VARCHAR(255) NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    CONSTRAINT fk_org_access_org 
        FOREIGN KEY (organization_id) 
        REFERENCES organizations(organization_id) ON DELETE CASCADE,
    
    CONSTRAINT fk_org_access_guideline 
        FOREIGN KEY (guideline_id) 
        REFERENCES organization_guidelines(guideline_id) ON DELETE CASCADE,
    
    UNIQUE(organization_id, guideline_id)
);

CREATE INDEX IF NOT EXISTS idx_org_guideline_access_org ON organization_guideline_access(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_guideline_access_guideline ON organization_guideline_access(guideline_id);
CREATE INDEX IF NOT EXISTS idx_org_guideline_access_granted_at ON organization_guideline_access(granted_at);

COMMENT ON TABLE organization_guideline_access IS 
'Admin-controlled mapping of which organizations can access which public guidelines';

COMMENT ON COLUMN organization_guideline_access.granted_by IS 
'Admin user email who granted this access';

COMMENT ON COLUMN organization_guideline_access.notes IS 
'Optional notes about why this access was granted';

-- ============================================================================
-- 3. Create guideline access audit log
-- ============================================================================

CREATE TABLE IF NOT EXISTS guideline_access_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    organization_id VARCHAR(255) NOT NULL,
    guideline_id VARCHAR(255) NOT NULL,
    access_granted BOOLEAN NOT NULL,
    access_reason VARCHAR(255),
    session_id VARCHAR(255),
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_guideline_access_user ON guideline_access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_guideline_access_email ON guideline_access_log(user_email);
CREATE INDEX IF NOT EXISTS idx_guideline_access_org ON guideline_access_log(organization_id);
CREATE INDEX IF NOT EXISTS idx_guideline_access_time ON guideline_access_log(accessed_at);

COMMENT ON TABLE guideline_access_log IS 
'Audit log of guideline access attempts for security and compliance';

-- ============================================================================
-- 4. Sample data: Organization email domain mappings
-- ============================================================================

-- Update existing organizations with email domains
UPDATE organizations 
SET email_domains = '["unicef.org", "unicef.ch"]'::jsonb
WHERE organization_id = 'org-unicef';

UPDATE organizations 
SET email_domains = '["gatesfoundation.org", "gates.com"]'::jsonb
WHERE organization_id = 'org-gates';

-- Insert ABCD public organization for universal guidelines
INSERT INTO organizations (
    organization_id, organization_name, email_domains, is_active, 
    description, created_at
) VALUES (
    'org-abcd-public',
    'ABCD Public Guidelines',
    '["abcd.org"]'::jsonb,
    TRUE,
    'Container for public guidelines available to multiple organizations',
    CURRENT_TIMESTAMP
) ON CONFLICT (organization_id) DO UPDATE
SET organization_name = EXCLUDED.organization_name,
    email_domains = EXCLUDED.email_domains,
    description = EXCLUDED.description;

-- ============================================================================
-- 5. Sample data: Universal public guideline
-- ============================================================================

INSERT INTO organization_guidelines (
    guideline_id, organization_id, guideline_name, guideline_text,
    description, is_public, visibility_scope, is_active, created_at
) VALUES (
    'guideline-universal-001',
    'org-abcd-public',
    'Universal Proposal Writing Guidelines',
    'These are general best practices for proposal writing that apply across all organizations:

1. Clear Problem Statement
   - Define the problem you are addressing
   - Use data and evidence to support the need
   - Explain why this problem matters now

2. Theory of Change
   - Show clear logical connections between activities and outcomes
   - Identify assumptions and risks
   - Define measurable indicators

3. Budget Justification
   - Align budget with proposed activities
   - Provide detailed cost breakdowns
   - Justify major expenses

4. Sustainability
   - Explain how benefits will continue after funding ends
   - Describe capacity building elements
   - Outline exit strategy

5. Monitoring & Evaluation
   - Define clear success metrics
   - Describe data collection methods
   - Explain how findings will inform decisions',
    'Universal guidelines available to all organizations',
    TRUE,
    'universal',
    TRUE,
    CURRENT_TIMESTAMP
) ON CONFLICT (guideline_id) DO UPDATE
SET guideline_name = EXCLUDED.guideline_name,
    guideline_text = EXCLUDED.guideline_text,
    description = EXCLUDED.description,
    is_public = EXCLUDED.is_public,
    visibility_scope = EXCLUDED.visibility_scope;

-- ============================================================================
-- 6. Mark some existing guidelines as public_mapped (if they exist)
-- ============================================================================

-- This is a safe update that will only affect guidelines that exist
UPDATE organization_guidelines 
SET is_public = TRUE, 
    visibility_scope = 'public_mapped'
WHERE guideline_name ILIKE '%best practices%' 
   OR guideline_name ILIKE '%template%'
   OR guideline_name ILIKE '%standard%';

-- ============================================================================
-- 7. Create helper function for checking guideline access
-- ============================================================================

CREATE OR REPLACE FUNCTION can_access_guideline(
    p_user_email VARCHAR,
    p_guideline_id VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_user_org VARCHAR;
    v_guideline_org VARCHAR;
    v_visibility VARCHAR;
    v_is_public BOOLEAN;
    v_has_access BOOLEAN;
BEGIN
    -- Get user's organization from email domain
    SELECT o.organization_id INTO v_user_org
    FROM organizations o
    WHERE o.is_active = TRUE
      AND o.email_domains IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM jsonb_array_elements_text(o.email_domains) domain
          WHERE LOWER(p_user_email) LIKE '%@' || LOWER(domain)
      )
    LIMIT 1;
    
    -- Get guideline info
    SELECT organization_id, visibility_scope, is_public
    INTO v_guideline_org, v_visibility, v_is_public
    FROM organization_guidelines
    WHERE guideline_id = p_guideline_id AND is_active = TRUE;
    
    -- If guideline doesn't exist or is inactive
    IF v_guideline_org IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Universal public guidelines - everyone can access
    IF v_is_public AND v_visibility = 'universal' THEN
        RETURN TRUE;
    END IF;
    
    -- If user has no organization, can only access universal
    IF v_user_org IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Organization's own guidelines
    IF v_guideline_org = v_user_org THEN
        RETURN TRUE;
    END IF;
    
    -- Public mapped - check explicit access grant
    IF v_is_public AND v_visibility = 'public_mapped' THEN
        SELECT EXISTS(
            SELECT 1 FROM organization_guideline_access
            WHERE organization_id = v_user_org
              AND guideline_id = p_guideline_id
        ) INTO v_has_access;
        
        RETURN v_has_access;
    END IF;
    
    -- Default deny
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION can_access_guideline IS 
'Check if a user can access a specific guideline based on their email domain and organization';

-- ============================================================================
-- 8. Create view for easy guideline access queries
-- ============================================================================

CREATE OR REPLACE VIEW v_guideline_access_summary AS
SELECT 
    g.guideline_id,
    g.guideline_name,
    g.organization_id as owner_org_id,
    o.organization_name as owner_org_name,
    g.visibility_scope,
    g.is_public,
    g.is_active,
    COUNT(DISTINCT oga.organization_id) as shared_with_count,
    ARRAY_AGG(DISTINCT oga.organization_id) FILTER (WHERE oga.organization_id IS NOT NULL) as shared_with_orgs
FROM organization_guidelines g
LEFT JOIN organizations o ON g.organization_id = o.organization_id
LEFT JOIN organization_guideline_access oga ON g.guideline_id = oga.guideline_id
GROUP BY g.guideline_id, g.guideline_name, g.organization_id, 
         o.organization_name, g.visibility_scope, g.is_public, g.is_active;

COMMENT ON VIEW v_guideline_access_summary IS 
'Summary view showing which guidelines are shared with which organizations';

-- ============================================================================
-- Migration complete
-- ============================================================================

-- Verify migration
DO $$ 
BEGIN
    RAISE NOTICE 'Migration 008 completed successfully!';
    RAISE NOTICE 'Organizations table: email_domains column added';
    RAISE NOTICE 'Guidelines table: is_public and visibility_scope columns added';
    RAISE NOTICE 'New table: organization_guideline_access';
    RAISE NOTICE 'New table: guideline_access_log';
    RAISE NOTICE 'New function: can_access_guideline()';
    RAISE NOTICE 'New view: v_guideline_access_summary';
END $$;
