-- Allow users to check their own admin status
CREATE POLICY "Users can check their own admin status"
ON public.admin_users
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Allow global admins to manage any organization credits
CREATE POLICY "Global admins can manage any organization credits"
ON public.organization_credits
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can insert their organization credit transactions via functions" ON public.organization_credit_transactions;

-- Only allow admins to insert transaction records directly
CREATE POLICY "Only admins can insert credit transaction logs"
ON public.organization_credit_transactions
FOR INSERT
TO authenticated
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
);

-- Allow global admins to view, update, and delete any organization credit transactions
CREATE POLICY "Global admins can manage any organization credit transactions"
ON public.organization_credit_transactions
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
);
