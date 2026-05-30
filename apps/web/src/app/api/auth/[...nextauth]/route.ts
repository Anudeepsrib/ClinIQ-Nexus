import NextAuth, { NextAuthOptions } from "next-auth"
import CognitoProvider from "next-auth/providers/cognito"

const authOptions: NextAuthOptions = {
  providers: [
    CognitoProvider({
      clientId: process.env.COGNITO_CLIENT_ID || "",
      clientSecret: process.env.COGNITO_CLIENT_SECRET || "",
      issuer: process.env.COGNITO_ISSUER || "",
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      // Map Cognito roles and tenant info into the NextAuth token
      if (account && profile) {
        token.accessToken = account.access_token
        token.idToken = account.id_token
        token.role = (profile as any)["custom:role"] || "user"
        token.tenantId = (profile as any)["custom:tenant_id"] || ""
      }
      return token
    },
    async session({ session, token }) {
      // Inject token properties into the session for frontend access
      if (session.user) {
        (session as any).accessToken = token.accessToken;
        (session as any).role = token.role;
        (session as any).tenantId = token.tenantId;
      }
      return session
    }
  },
  pages: {
    signIn: '/auth/signin',
  }
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }
