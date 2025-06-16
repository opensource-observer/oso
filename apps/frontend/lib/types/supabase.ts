export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
      admin_users: {
        Row: {
          created_at: string;
          description: string | null;
          id: number;
          name: string;
          updated_at: string;
          user_id: string;
        };
        Insert: {
          created_at?: string;
          description?: string | null;
          id?: number;
          name: string;
          updated_at?: string;
          user_id: string;
        };
        Update: {
          created_at?: string;
          description?: string | null;
          id?: number;
          name?: string;
          updated_at?: string;
          user_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "admin_users_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
        ];
      };
      api_keys: {
        Row: {
          api_key: string;
          created_at: string;
          deleted_at: string | null;
          id: string;
          name: string;
          org_id: string;
          updated_at: string;
          user_id: string;
        };
        Insert: {
          api_key: string;
          created_at?: string;
          deleted_at?: string | null;
          id?: string;
          name: string;
          org_id: string;
          updated_at?: string;
          user_id: string;
        };
        Update: {
          api_key?: string;
          created_at?: string;
          deleted_at?: string | null;
          id?: string;
          name?: string;
          org_id?: string;
          updated_at?: string;
          user_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "api_keys_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "api_keys_user_id_fkey1";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
        ];
      };
      chat_history: {
        Row: {
          created_at: string;
          created_by: string;
          data: string | null;
          deleted_at: string | null;
          display_name: string;
          id: string;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          created_by: string;
          data?: string | null;
          deleted_at?: string | null;
          display_name: string;
          id?: string;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          created_by?: string;
          data?: string | null;
          deleted_at?: string | null;
          display_name?: string;
          id?: string;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "chat_history_created_by_fkey";
            columns: ["created_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "chat_history_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      connector_relationships: {
        Row: {
          id: string;
          org_id: string;
          source_column_name: string;
          source_table_id: string;
          target_column_name: string | null;
          target_oso_entity: string | null;
          target_table_id: string | null;
        };
        Insert: {
          id?: string;
          org_id: string;
          source_column_name: string;
          source_table_id: string;
          target_column_name?: string | null;
          target_oso_entity?: string | null;
          target_table_id?: string | null;
        };
        Update: {
          id?: string;
          org_id?: string;
          source_column_name?: string;
          source_table_id?: string;
          target_column_name?: string | null;
          target_oso_entity?: string | null;
          target_table_id?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "fk_org_id";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "fk_source_column";
            columns: ["source_table_id", "source_column_name"];
            isOneToOne: false;
            referencedRelation: "dynamic_column_contexts";
            referencedColumns: ["table_id", "column_name"];
          },
          {
            foreignKeyName: "fk_source_table";
            columns: ["source_table_id"];
            isOneToOne: false;
            referencedRelation: "dynamic_table_contexts";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "fk_target_column";
            columns: ["target_table_id", "target_column_name"];
            isOneToOne: false;
            referencedRelation: "dynamic_column_contexts";
            referencedColumns: ["table_id", "column_name"];
          },
          {
            foreignKeyName: "fk_target_table";
            columns: ["target_table_id"];
            isOneToOne: false;
            referencedRelation: "dynamic_table_contexts";
            referencedColumns: ["id"];
          },
        ];
      };
      credit_transactions: {
        Row: {
          amount: number;
          api_endpoint: string | null;
          created_at: string;
          id: string;
          metadata: Json | null;
          transaction_type: string;
          user_id: string;
        };
        Insert: {
          amount: number;
          api_endpoint?: string | null;
          created_at?: string;
          id?: string;
          metadata?: Json | null;
          transaction_type: string;
          user_id: string;
        };
        Update: {
          amount?: number;
          api_endpoint?: string | null;
          created_at?: string;
          id?: string;
          metadata?: Json | null;
          transaction_type?: string;
          user_id?: string;
        };
        Relationships: [];
      };
      dynamic_column_contexts: {
        Row: {
          column_name: string;
          data_type: string;
          description: string | null;
          sample_data: string | null;
          table_id: string;
        };
        Insert: {
          column_name: string;
          data_type: string;
          description?: string | null;
          sample_data?: string | null;
          table_id: string;
        };
        Update: {
          column_name?: string;
          data_type?: string;
          description?: string | null;
          sample_data?: string | null;
          table_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "fk_table_context";
            columns: ["table_id"];
            isOneToOne: false;
            referencedRelation: "dynamic_table_contexts";
            referencedColumns: ["id"];
          },
        ];
      };
      dynamic_connectors: {
        Row: {
          config: Json | null;
          connector_name: string;
          connector_type: string;
          created_at: string;
          created_by: string;
          deleted_at: string | null;
          id: string;
          is_public: boolean | null;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          config?: Json | null;
          connector_name: string;
          connector_type: string;
          created_at?: string;
          created_by: string;
          deleted_at?: string | null;
          id?: string;
          is_public?: boolean | null;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          config?: Json | null;
          connector_name?: string;
          connector_type?: string;
          created_at?: string;
          created_by?: string;
          deleted_at?: string | null;
          id?: string;
          is_public?: boolean | null;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "fk_org_id";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      dynamic_table_contexts: {
        Row: {
          connector_id: string;
          description: string | null;
          id: string;
          table_name: string;
        };
        Insert: {
          connector_id: string;
          description?: string | null;
          id?: string;
          table_name: string;
        };
        Update: {
          connector_id?: string;
          description?: string | null;
          id?: string;
          table_name?: string;
        };
        Relationships: [
          {
            foreignKeyName: "fk_connector_id";
            columns: ["connector_id"];
            isOneToOne: false;
            referencedRelation: "dynamic_connectors";
            referencedColumns: ["id"];
          },
        ];
      };
      organizations: {
        Row: {
          created_at: string;
          created_by: string;
          deleted_at: string | null;
          id: string;
          org_name: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          created_by: string;
          deleted_at?: string | null;
          id?: string;
          org_name: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          created_by?: string;
          deleted_at?: string | null;
          id?: string;
          org_name?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "organizations_created_by_fkey1";
            columns: ["created_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
        ];
      };
      purchase_intents: {
        Row: {
          completed_at: string | null;
          created_at: string;
          credits_amount: number;
          id: string;
          metadata: Json | null;
          package_id: string;
          price_cents: number;
          status: string;
          stripe_session_id: string;
          user_id: string;
        };
        Insert: {
          completed_at?: string | null;
          created_at?: string;
          credits_amount: number;
          id?: string;
          metadata?: Json | null;
          package_id: string;
          price_cents: number;
          status?: string;
          stripe_session_id: string;
          user_id: string;
        };
        Update: {
          completed_at?: string | null;
          created_at?: string;
          credits_amount?: number;
          id?: string;
          metadata?: Json | null;
          package_id?: string;
          price_cents?: number;
          status?: string;
          stripe_session_id?: string;
          user_id?: string;
        };
        Relationships: [];
      };
      saved_queries: {
        Row: {
          created_at: string;
          created_by: string;
          data: string | null;
          deleted_at: string | null;
          display_name: string;
          id: string;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          created_by: string;
          data?: string | null;
          deleted_at?: string | null;
          display_name: string;
          id?: string;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          created_by?: string;
          data?: string | null;
          deleted_at?: string | null;
          display_name?: string;
          id?: string;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "saved_queries_created_by_fkey";
            columns: ["created_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "saved_queries_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      user_credits: {
        Row: {
          created_at: string;
          credits_balance: number;
          id: string;
          updated_at: string;
          user_id: string;
        };
        Insert: {
          created_at?: string;
          credits_balance?: number;
          id?: string;
          updated_at?: string;
          user_id: string;
        };
        Update: {
          created_at?: string;
          credits_balance?: number;
          id?: string;
          updated_at?: string;
          user_id?: string;
        };
        Relationships: [];
      };
      user_profiles: {
        Row: {
          avatar_url: string | null;
          email: string | null;
          full_name: string | null;
          id: string;
          updated_at: string | null;
          username: string | null;
          website: string | null;
        };
        Insert: {
          avatar_url?: string | null;
          email?: string | null;
          full_name?: string | null;
          id: string;
          updated_at?: string | null;
          username?: string | null;
          website?: string | null;
        };
        Update: {
          avatar_url?: string | null;
          email?: string | null;
          full_name?: string | null;
          id?: string;
          updated_at?: string | null;
          username?: string | null;
          website?: string | null;
        };
        Relationships: [];
      };
      users_by_organization: {
        Row: {
          created_at: string;
          deleted_at: string | null;
          id: string;
          org_id: string;
          updated_at: string;
          user_id: string;
          user_role: string;
        };
        Insert: {
          created_at?: string;
          deleted_at?: string | null;
          id?: string;
          org_id: string;
          updated_at?: string;
          user_id: string;
          user_role: string;
        };
        Update: {
          created_at?: string;
          deleted_at?: string | null;
          id?: string;
          org_id?: string;
          updated_at?: string;
          user_id?: string;
          user_role?: string;
        };
        Relationships: [
          {
            foreignKeyName: "users_by_organization_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "users_by_organization_user_id_fkey1";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
        ];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      add_credits: {
        Args: {
          p_user_id: string;
          p_amount: number;
          p_transaction_type: string;
          p_metadata?: Json;
        };
        Returns: boolean;
      };
      deduct_credits: {
        Args: {
          p_user_id: string;
          p_amount: number;
          p_transaction_type: string;
          p_api_endpoint?: string;
          p_metadata?: Json;
        };
        Returns: boolean;
      };
      get_user_credits: {
        Args: { p_user_id: string };
        Returns: number;
      };
      hasura_token_hook: {
        Args: { event: Json };
        Returns: Json;
      };
      preview_deduct_credits: {
        Args: {
          p_user_id: string;
          p_amount: number;
          p_transaction_type: string;
          p_api_endpoint?: string;
          p_metadata?: Json;
        };
        Returns: boolean;
      };
    };
    Enums: {
      [_ in never]: never;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

type DefaultSchema = Database[Extract<keyof Database, "public">];

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R;
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R;
      }
      ? R
      : never
    : never;

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I;
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I;
      }
      ? I
      : never
    : never;

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U;
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U;
      }
      ? U
      : never
    : never;

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof Database },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never;

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof Database },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof Database }
  ? Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never;

export const Constants = {
  public: {
    Enums: {},
  },
} as const;
