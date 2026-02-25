/**
 * AutoYield Policy Engine
 * Handles autonomous transaction governance and safety limits.
 */

export interface TransactionRequest {
    target: string;
    amountLamports: number;
    currentBalanceLamports: number;
}

export interface PolicyResult {
    isAllowed: boolean;
    reason?: string;
}

export class PolicyEngine {
    private readonly MAX_TX_AMOUNT_SOL = 1.0;
    private readonly DAILY_LIMIT_SOL = 5.0;
    private totalSpentTodaySOL = 0;

    /**
     * Evaluates a transaction request against safety policies.
     */
    public evaluate(request: TransactionRequest): PolicyResult {
        const amountSOL = request.amountLamports / 1e9;

        // 1. Check maximum single transaction size
        if (amountSOL > this.MAX_TX_AMOUNT_SOL) {
            return {
                isAllowed: false,
                reason: `Exceeds maximum single transaction limit of ${this.MAX_TX_AMOUNT_SOL} SOL`,
            };
        }

        // 2. Check daily budget
        if (this.totalSpentTodaySOL + amountSOL > this.DAILY_LIMIT_SOL) {
            return {
                isAllowed: false,
                reason: `Exceeds daily budget of ${this.DAILY_LIMIT_SOL} SOL`,
            };
        }

        // 3. Ensure sufficient remaining balance (safety buffer)
        const safetyBuffer = 0.05 * 1e9; // 0.05 SOL buffer
        if (request.currentBalanceLamports - request.amountLamports < safetyBuffer) {
            return {
                isAllowed: false,
                reason: "Insufficient remaining balance for gas safety buffer",
            };
        }

        // Update state (in a real app, this would be persisted)
        this.totalSpentTodaySOL += amountSOL;

        return { isAllowed: true };
    }

    public resetDailyLimit(): void {
        this.totalSpentTodaySOL = 0;
    }
}
